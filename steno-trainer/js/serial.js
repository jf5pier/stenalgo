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

  if (!("serial" in navigator)) {
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
  app.ports.requestConnect.subscribe(connect);

  navigator.serial.addEventListener("disconnect", function () {
    sendStatus("disconnected");
  });
})();
