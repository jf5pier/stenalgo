port module Ports exposing (incomingBytes, incomingHidChord, requestConnect, requestConnectHid, saveSettings, serialStatus)

{-| The boundary to `js/serial.js` -- the only hand-written JS in this app,
kept deliberately dumb (raw port/byte I/O only, no protocol decoding; see
`GeminiPr.elm` for that).
-}


{-| Elm -> JS: call `navigator.serial.requestPort()` from a click handler.
-}
port requestConnect : () -> Cmd msg


{-| JS -> Elm: one raw 6-byte Gemini PR packet per completed stroke, already
framed/resynced by `js/serial.js`'s read loop but not yet decoded.
-}
port incomingBytes : (List Int -> msg) -> Sub msg


{-| JS -> Elm: "unsupported" (no `navigator.serial`), "connected",
"disconnected", or "error:<message>".
-}
port serialStatus : (String -> msg) -> Sub msg


{-| Elm -> JS: call `navigator.hid.requestDevice()` (Plover HID machines) from
a click handler.
-}
port requestConnectHid : () -> Cmd msg


{-| JS -> Elm: one completed chord from a Plover HID machine, as the 8 bytes
(64 key bits, big-endian) ORed over the press; decoded by `PloverHid`.
-}
port incomingHidChord : (List Int -> msg) -> Sub msg


{-| Elm -> JS: the sidebar settings as a JSON string, to store in the `stenalgo_settings`
cookie (and, for the dark mode, to switch the page's theme class). Read back at start-up as
the `settings` flag.
-}
port saveSettings : String -> Cmd msg
