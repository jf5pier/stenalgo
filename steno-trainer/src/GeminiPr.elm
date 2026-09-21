module GeminiPr exposing (decodePacket, stenoKeyChart)

{-| Decoding for the Gemini PR wire protocol -- the same protocol real Plover
reads over a serial connection from Gemini-PR-compatible steno machines
(including the Starboard). Ported directly from Plover 5.4.1's
`plover/machine/gemini_pr.py`, confirmed against that source this session.

One 6-byte packet is sent per **completed stroke** (the machine's own firmware
assembles the full chord before sending, not a keydown/keyup stream): byte 0
has the 0x80 framing bit set, bytes 1-5 don't. Each byte's remaining 7 bits
(0x40 down to 0x01) each flag one entry of `stenoKeyChart`, 7 entries per byte,
42 total.
-}

import Bitwise


stenoKeyChart : List String
stenoKeyChart =
    [ "Fn", "#1", "#2", "#3", "#4", "#5", "#6"
    , "S1-", "S2-", "T-", "K-", "P-", "W-", "H-"
    , "R-", "A-", "O-", "*1", "*2", "res1", "res2"
    , "pwr", "*3", "*4", "-E", "-U", "-F", "-R"
    , "-P", "-B", "-L", "-G", "-T", "-S", "-D"
    , "#7", "#8", "#9", "#A", "#B", "#C", "-Z"
    ]


{-| Decode a raw 6-byte Gemini PR packet into the labels of the keys held in
that stroke.
-}
decodePacket : List Int -> Result String (List String)
decodePacket packet =
    case packet of
        [ b0, b1, b2, b3, b4, b5 ] ->
            if Bitwise.and b0 0x80 /= 0x80 then
                Err "byte 0 missing the 0x80 framing bit"

            else if List.any (\b -> Bitwise.and b 0x80 /= 0) [ b1, b2, b3, b4, b5 ] then
                Err "byte 1-5 unexpectedly has the 0x80 framing bit set"

            else
                Ok (List.concat (List.indexedMap decodeByte packet))

        _ ->
            Err ("expected a 6-byte packet, got " ++ String.fromInt (List.length packet) ++ " bytes")


decodeByte : Int -> Int -> List String
decodeByte byteIndex byte =
    List.range 1 7
        |> List.filterMap
            (\j ->
                if Bitwise.and byte (Bitwise.shiftRightBy j 0x80) /= 0 then
                    List.drop (byteIndex * 7 + j - 1) stenoKeyChart |> List.head

                else
                    Nothing
            )
