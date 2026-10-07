// The only hand-written JS in this app. Deliberately dumb: it does raw
// navigator.serial plumbing and packet framing/resync only. All protocol
// decoding (Gemini PR chart lookup, stroke matching, drill state) lives in
// Elm (see src/GeminiPr.elm, src/Drill.elm) -- this file just hands 6-byte
// packets across the `incomingBytes` port.
//
// Known limitations (see steno-trainer/README.md):
// - Chromium-only (navigator.serial doesn't exist in Firefox/Safari).
// - Requires a secure context (HTTPS or localhost, not file://).
// - requestPort() must be called from a direct click handler (see below).
(function () {
  var app = Elm.Main.init({ node: document.getElementById("app") });

  function sendStatus(status) {
    app.ports.serialStatus.send(status);
  }

  var hasSerial = "serial" in navigator;
  var hasHid = "hid" in navigator;
  if (!hasSerial && !hasHid) {
    sendStatus("unsupported");
    return;
  }

  // Scans `buffer` for complete 6-byte Gemini PR packets (byte 0 has the
  // 0x80 framing bit set, bytes 1-5 don't), forwarding each one found to Elm
  // for decoding. On a framing mismatch, drops just the candidate start byte
  // and rescans from the next byte, so one corrupted byte can't permanently
  // desync the stream. Returns the leftover, not-yet-consumable tail.
  function consumePackets(buffer) {
    var i = 0;
    while (i < buffer.length) {
      if ((buffer[i] & 0x80) === 0) {
        i += 1;
        continue;
      }
      if (i + 6 > buffer.length) {
        break; // wait for more bytes
      }
      var candidate = buffer.slice(i, i + 6);
      var restClear = candidate.slice(1).every(function (b) {
        return (b & 0x80) === 0;
      });
      if (restClear) {
        app.ports.incomingBytes.send(candidate);
        i += 6;
      } else {
        i += 1; // resync: drop just the candidate start byte
      }
    }
    return buffer.slice(i);
  }

  async function readLoop(port) {
    var reader = port.readable.getReader();
    var buffer = [];
    try {
      while (true) {
        var result = await reader.read();
        if (result.done) {
          break;
        }
        for (var j = 0; j < result.value.length; j++) {
          buffer.push(result.value[j]);
        }
        buffer = consumePackets(buffer);
      }
    } catch (err) {
      sendStatus("error:" + err.message);
    } finally {
      reader.releaseLock();
      sendStatus("disconnected");
    }
  }

  async function connect() {
    try {
      var port = await navigator.serial.requestPort();
      await port.open({ baudRate: 9600 });
      sendStatus("connected");
      readLoop(port);
    } catch (err) {
      sendStatus("error:" + err.message);
    }
  }

  // Elm calls this only from a button click handler, satisfying Web
  // Serial's user-gesture requirement for requestPort().
  app.ports.requestConnect.subscribe(function () {
    if (!hasSerial) {
      sendStatus("error:Web Serial is not available in this browser");
      return;
    }
    connect();
  });

  if (hasSerial) {
    navigator.serial.addEventListener("disconnect", function () {
      sendStatus("disconnected");
    });
  }

  // --- Plover HID (WebHID) -------------------------------------------------
  // The device sends its whole key state on every change (report id 0x50,
  // then 8 bytes = 64 key bits, see Plover HID / plover-machine-hid). Like
  // Plover's default (no first-up) mode, the keys seen since the last
  // all-released report are ORed together and the chord is handed to Elm
  // (port `incomingHidChord`, 8 bytes) when every key is up again.
  var HID_USAGE_PAGE = 0xff50;
  var HID_USAGE = 0x4c56;
  var HID_REPORT_ID = 0x50;

  function watchHid(device) {
    var chord = [0, 0, 0, 0, 0, 0, 0, 0];
    device.addEventListener("inputreport", function (event) {
      if (event.reportId !== HID_REPORT_ID || event.data.byteLength < 8) {
        return;
      }
      var any = false;
      for (var k = 0; k < 8; k++) {
        var b = event.data.getUint8(k);
        chord[k] |= b;
        any = any || b !== 0;
      }
      if (!any) {
        app.ports.incomingHidChord.send(chord);
        chord = [0, 0, 0, 0, 0, 0, 0, 0];
      }
    });
  }

  async function connectHid() {
    if (!hasHid) {
      sendStatus("error:WebHID is not available in this browser");
      return;
    }
    try {
      var devices = await navigator.hid.requestDevice({
        filters: [{ usagePage: HID_USAGE_PAGE, usage: HID_USAGE }],
      });
      if (devices.length === 0) {
        sendStatus("error:no Plover HID device chosen or found (is Plover holding it?)");
        return;
      }
      var device = devices[0];
      if (!device.opened) {
        await device.open();
      }
      watchHid(device);
      sendStatus("connected");
    } catch (err) {
      sendStatus("error:" + err.message);
    }
  }

  app.ports.requestConnectHid.subscribe(connectHid);

  if (hasHid) {
    navigator.hid.addEventListener("disconnect", function () {
      sendStatus("disconnected");
    });
  }
})();
