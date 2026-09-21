module Keyboard exposing (KeyInfo, decoder, geminiKeymap, view)

{-| The virtual Starboard: decodes `keyboard-layout.json` (exported by
`util/export_keyboard_layout.py` from the repo's own `Starboard` class) and
renders it as a grid, highlighting the keys a given stroke expects/matches.
-}

import Dict exposing (Dict)
import Html exposing (Html, div, text)
import Html.Attributes exposing (class, classList, style)
import Json.Decode as D
import Json.Decode.Pipeline exposing (required)
import Set exposing (Set)


type alias KeyInfo =
    { index : Int
    , name : String
    , hand : String
    , finger : String
    , row : Int
    , col : Int
    , part : Maybe String
    , reserved : Bool
    , geminiPrLabel : String
    }


keyInfoDecoder : D.Decoder KeyInfo
keyInfoDecoder =
    D.succeed KeyInfo
        |> required "index" D.int
        |> required "name" D.string
        |> required "hand" D.string
        |> required "finger" D.string
        |> required "row" D.int
        |> required "col" D.int
        |> required "part" (D.nullable D.string)
        |> required "reserved" D.bool
        |> required "geminiPrLabel" D.string


decoder : D.Decoder (List KeyInfo)
decoder =
    D.field "keys" (D.list keyInfoDecoder)


{-| Gemini PR label -> Stenalgo key index, built from the same data the
keyboard view renders, so the two can never drift apart.
-}
geminiKeymap : List KeyInfo -> Dict String Int
geminiKeymap keys =
    keys
        |> List.map (\k -> ( k.geminiPrLabel, k.index ))
        |> Dict.fromList


{-| One CSS-grid cell per key: two rows for each side's onset/coda bank, plus
a third row for the thumb clusters and off-home index keys -- close enough to
`Starboard._printableKeyLayout`'s ASCII shape for a first virtual keyboard,
laid out per key by `hand`/`row`/`col` rather than any fixed template.
-}
view : { highlighted : Set Int, correct : Maybe Bool } -> List KeyInfo -> Html msg
view { highlighted, correct } keys =
    div [ class "keyboard" ]
        [ div [ class "hand hand-left" ] (List.filter (\k -> k.hand == "left") keys |> List.map (keyView highlighted correct))
        , div [ class "hand hand-right" ] (List.filter (\k -> k.hand == "right") keys |> List.map (keyView highlighted correct))
        ]


keyView : Set Int -> Maybe Bool -> KeyInfo -> Html msg
keyView highlighted correct key =
    let
        isHighlighted =
            Set.member key.index highlighted
    in
    div
        [ classList
            [ ( "key", True )
            , ( "key-reserved", key.reserved )
            , ( "key-expected", isHighlighted )
            , ( "key-correct", isHighlighted && correct == Just True )
            , ( "key-incorrect", isHighlighted && correct == Just False )
            ]
        , style "grid-row" (String.fromInt (key.row + 1))
        , style "grid-column" (String.fromInt (key.col + 1))
        ]
        [ text key.name ]
