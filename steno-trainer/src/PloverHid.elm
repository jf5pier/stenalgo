module PloverHid exposing (decodeChord, stenoKeyChart)

{-| Decoding for the Plover HID chord reported by `js/serial.js` -- the same
bit layout as `plover-machine-hid`'s `STENO_KEY_CHART` (key `i` is bit
`63 - i` of the big-endian 64-bit state). The labels are the Gemini PR names
for the keys both protocols share, so `Keyboard.geminiKeymap` serves both.
-}

import Bitwise


stenoKeyChart : List String
stenoKeyChart =
    [ "S1-", "T-", "K-", "P-", "W-", "H-"
    , "R-", "A-", "O-", "*1", "-E", "-U"
    , "-F", "-R", "-P", "-B", "-L", "-G"
    , "-T", "-S", "-D", "-Z", "#1"
    , "S2-", "*2", "*3", "*4", "#2", "#3"
    , "#4", "#5", "#6", "#7", "#8", "#9"
    , "#A", "#B", "#C"
    ]


{-| Decode the 8 state bytes into the labels of the keys held (the extra
`X1`-`X26` keys are ignored: the chart stops at `#C`).
-}
decodeChord : List Int -> Result String (List String)
decodeChord bytes =
    if List.length bytes /= 8 then
        Err ("expected 8 bytes, got " ++ String.fromInt (List.length bytes))

    else
        Ok
            (stenoKeyChart
                |> List.indexedMap Tuple.pair
                |> List.filterMap
                    (\( i, label ) ->
                        let
                            byte =
                                List.drop (i // 8) bytes |> List.head |> Maybe.withDefault 0
                        in
                        if Bitwise.and byte (Bitwise.shiftRightBy (modBy 8 i) 0x80) /= 0 then
                            Just label

                        else
                            Nothing
                    )
            )
