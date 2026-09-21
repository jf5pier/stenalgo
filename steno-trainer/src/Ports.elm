port module Ports exposing (incomingBytes, requestConnect, serialStatus)

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
