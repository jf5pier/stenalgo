module Keyboard exposing (KeyInfo, Layout, decoder, geminiKeymap, view, viewChordBoard, viewLegends)

{-| The virtual Starboard: decodes `keyboard-layout.json` (exported by
`util/export_keyboard_layout.py` from the repo's own `Starboard` class) and
renders it as a grid, highlighting the keys a given stroke expects/matches.
Also renders the reference material the export includes alongside the
geometry -- the 2-key chord layer as a second, static keyboard (`viewChordBoard`,
mirroring `Starboard.printLayout`'s own "N-key phonemes layer" boards), and the
sparser 3-/4-key thumb chords plus the same-lemma/conjugation marker keys
(Phase P; see `src/ambiguitychecker.py`) as plain-text legends (`viewLegends`).
-}

import Dict exposing (Dict)
import Html exposing (Html, div, h3, li, text, ul)
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


type alias PhonemeStroke =
    { keys : List Int
    , phonemes : String
    }


type alias PhonemeLayer =
    { keyCount : Int
    , phonemesByKey : Dict Int String
    , strokes : List PhonemeStroke
    }


{-| One same-lemma/conjugation marker group (Phase P): the physical key(s)
chosen for it, and a French label for the grammatical features it marks (e.g.
"impératif, 1re personne" on key "-k"). Distinct from the `*`/`#` keys, which
mark different *lemmas* that happen to sound alike, not inflected forms of one.
-}
type alias ConjugationMarker =
    { keys : List Int
    , keyNames : List String
    , label : String
    }


type alias Layout =
    { keys : List KeyInfo
    , phonemeLayers : List PhonemeLayer
    , conjugationMarkers : List ConjugationMarker
    }


phonemeStrokeDecoder : D.Decoder PhonemeStroke
phonemeStrokeDecoder =
    D.map2 PhonemeStroke
        (D.field "keys" (D.list D.int))
        (D.field "phonemes" D.string)


phonemeLayerDecoder : D.Decoder PhonemeLayer
phonemeLayerDecoder =
    D.map3 PhonemeLayer
        (D.field "keyCount" D.int)
        (D.field "phonemesByKey" (D.dict D.string) |> D.map intKeyedDict)
        (D.field "strokes" (D.list phonemeStrokeDecoder))


intKeyedDict : Dict String String -> Dict Int String
intKeyedDict =
    Dict.foldl
        (\k v acc ->
            case String.toInt k of
                Just i ->
                    Dict.insert i v acc

                Nothing ->
                    acc
        )
        Dict.empty


conjugationMarkerDecoder : D.Decoder ConjugationMarker
conjugationMarkerDecoder =
    D.map3 ConjugationMarker
        (D.field "keys" (D.list D.int))
        (D.field "keyNames" (D.list D.string))
        (D.field "label" D.string)


decoder : D.Decoder Layout
decoder =
    D.map3 Layout
        (D.field "keys" (D.list keyInfoDecoder))
        (D.field "phonemeLayers" (D.list phonemeLayerDecoder))
        (D.field "conjugationMarkers" (D.list conjugationMarkerDecoder))


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


{-| The second, non-interactive board for the 2-key chord layer: same shape
as `view`'s, just overlaid with each key's chord phonemes instead of its
single-key name (`Starboard.printLayout`'s "2-key phonemes layer" board).
-}
viewChordBoard : Layout -> Html msg
viewChordBoard layout =
    case List.filter (\l -> l.keyCount == 2) layout.phonemeLayers of
        layer :: _ ->
            div [ class "phoneme-layer" ]
                [ h3 [] [ text "Second keyboard: 2-key stroke phonemes" ]
                , viewLayerGrid layout.keys layer.phonemesByKey
                ]

        [] ->
            text ""


viewLayerGrid : List KeyInfo -> Dict Int String -> Html msg
viewLayerGrid keys phonemesByKey =
    div [ class "keyboard keyboard-reference" ]
        [ div [ class "hand hand-left" ] (List.filter (\k -> k.hand == "left") keys |> List.map (layerKeyView phonemesByKey))
        , div [ class "hand hand-right" ] (List.filter (\k -> k.hand == "right") keys |> List.map (layerKeyView phonemesByKey))
        ]


layerKeyView : Dict Int String -> KeyInfo -> Html msg
layerKeyView phonemesByKey key =
    div
        [ classList
            [ ( "key", True )
            , ( "key-reserved", key.reserved )
            ]
        , style "grid-row" (String.fromInt (key.row + 1))
        , style "grid-column" (String.fromInt (key.col + 1))
        ]
        [ text (Dict.get key.index phonemesByKey |> Maybe.withDefault "") ]


{-| The two plain-text legends too sparse/small to draw as a board: the
3-/4-key thumb-only chords, and the same-lemma/conjugation marker keys.
Meant for a narrow sidebar column next to the page title, not stacked under
the (tall) keyboards.
-}
viewLegends : Layout -> Html msg
viewLegends layout =
    div [ class "legends" ]
        [ viewStrokeLegend layout.keys (List.filter (\l -> l.keyCount > 2) layout.phonemeLayers)
        , viewConjugationLegend layout.conjugationMarkers
        ]


viewStrokeLegend : List KeyInfo -> List PhonemeLayer -> Html msg
viewStrokeLegend keys layers =
    div [ class "legend-block" ]
        [ h3 [] [ text "3- and 4-key strokes" ]
        , ul [ class "legend" ]
            (layers
                |> List.concatMap .strokes
                |> List.map (viewStrokeLegendItem keys)
            )
        ]


viewStrokeLegendItem : List KeyInfo -> PhonemeStroke -> Html msg
viewStrokeLegendItem keys stroke =
    li []
        [ text (String.join " + " (List.map (keyLabel keys) stroke.keys) ++ " \u{2192} " ++ stroke.phonemes) ]


keyLabel : List KeyInfo -> Int -> String
keyLabel keys index =
    keys
        |> List.filter (\k -> k.index == index)
        |> List.head
        |> Maybe.map .name
        |> Maybe.withDefault (String.fromInt index)


viewConjugationLegend : List ConjugationMarker -> Html msg
viewConjugationLegend markers =
    div [ class "legend-block" ]
        [ h3 [] [ text "Conjugation markers" ]
        , ul [ class "legend" ]
            (markers
                |> List.map (\m -> li [] [ text (String.join "+" m.keyNames ++ " : " ++ m.label) ])
            )
        ]
