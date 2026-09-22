module Definitions exposing (Definitions, decoder, view)

{-| Definition mode: type a spelling, get every word sharing a base chord
with it -- its homophones, the words the conjugation marks and the `*`/`#`
track have to tell apart -- each with its reading(s), pronunciation and final
chord(s). Data from `util/export_definitions.py` (`definitions.json`),
which covers the whole lexicon, so it's only fetched when this mode is first
opened.
-}

import Array exposing (Array)
import Dict exposing (Dict)
import Html exposing (Html, h3, p, table, tbody, td, text, th, thead, tr)
import Html.Attributes exposing (class, classList)
import Json.Decode as D
import Set


type alias Chord =
    { steno : String
    , label : String
    }


type alias Entry =
    { ortho : String
    , phonology : String
    , frequency : Float
    , chords : List Chord
    }


{-| Every word typed with one base (phoneme-only) chord, most frequent first. -}
type alias Group =
    { base : String
    , entries : List Entry
    }


type alias Definitions =
    { groups : Array Group
    , groupsByOrtho : Dict String (List Int)
    }


{-| The export's positional arrays (see `util/export_definitions.py`), with
reading labels stored once in a shared table and referenced by index. -}
decoder : D.Decoder Definitions
decoder =
    D.field "labels" (D.array D.string)
        |> D.andThen (\labels -> D.field "groups" (D.array (groupDecoder labels)))
        |> D.map
            (\groups ->
                { groups = groups
                , groupsByOrtho =
                    Array.foldl
                        (\group ( index, acc ) ->
                            ( index + 1
                            , List.foldl
                                (\entry byOrtho ->
                                    Dict.update entry.ortho
                                        (\existing ->
                                            case existing of
                                                Just (latest :: rest) ->
                                                    if latest == index then
                                                        existing

                                                    else
                                                        Just (index :: latest :: rest)

                                                _ ->
                                                    Just [ index ]
                                        )
                                        byOrtho
                                )
                                acc
                                group.entries
                            )
                        )
                        ( 0, Dict.empty )
                        groups
                        |> Tuple.second
                }
            )


groupDecoder : Array String -> D.Decoder Group
groupDecoder labels =
    D.map2 Group
        (D.index 0 D.string)
        (D.index 1 (D.list (entryDecoder labels)))


entryDecoder : Array String -> D.Decoder Entry
entryDecoder labels =
    D.map4 Entry
        (D.index 0 D.string)
        (D.index 1 D.string)
        (D.index 2 D.float)
        (D.index 3 (D.list (chordDecoder labels)))


chordDecoder : Array String -> D.Decoder Chord
chordDecoder labels =
    D.map2 Chord
        (D.index 0 D.string)
        (D.index 1 D.int |> D.map (\i -> Array.get i labels |> Maybe.withDefault ""))


{-| The results for `query` (a spelling, case-insensitive): one table per
base chord the spelling is typed with ("est" has two: the verb and the
noun). `render` switches phonemes between X-SAMPA and IPA. A row whose
pronunciation differs from the searched word's is a near-homophone: a word
the layout happens to fold onto the same keys (e.g. /e/ and /O/ share one),
which needs its marks just the same.
-}
view : (String -> String) -> String -> Definitions -> Html msg
view render query definitions =
    let
        spelling =
            String.toLower (String.trim query)

        groups =
            Dict.get spelling definitions.groupsByOrtho
                |> Maybe.withDefault []
                |> List.reverse
                |> List.filterMap (\index -> Array.get index definitions.groups)
    in
    if String.isEmpty spelling then
        p [ class "definition-hint" ] [ text "Type a word's spelling to see its homophones, readings and chords." ]

    else if List.isEmpty groups then
        p [ class "definition-hint" ] [ text ("No word spelled \u{201C}" ++ spelling ++ "\u{201D} in the dictionary.") ]

    else
        Html.div [] (List.map (viewGroup render spelling) groups)


viewGroup : (String -> String) -> String -> Group -> Html msg
viewGroup render spelling group =
    let
        searchedPhonologies =
            group.entries |> List.filter (\e -> e.ortho == spelling) |> List.map .phonology |> Set.fromList

        entryRows entry =
            let
                nearHomophone =
                    not (Set.member entry.phonology searchedPhonologies)
            in
            List.indexedMap
                (\i chord ->
                    tr [ classList [ ( "searched", entry.ortho == spelling ), ( "near-homophone", nearHomophone ) ] ]
                        [ td [] [ text (ifFirst i entry.ortho) ]
                        , td [] [ text (ifFirst i ("/" ++ render entry.phonology ++ "/")) ]
                        , td [ class "definition-steno" ] [ text (render chord.steno) ]
                        , td [] [ text chord.label ]
                        ]
                )
                entry.chords
    in
    Html.div [ class "definition-group" ]
        [ h3 [] [ text ("Base chord " ++ render group.base) ]
        , table [ class "definition-table" ]
            [ thead [] [ tr [] [ th [] [ text "Word" ], th [] [ text "Pronunciation" ], th [] [ text "Chord" ], th [] [ text "Reading" ] ] ]
            , tbody [] (List.concatMap entryRows group.entries)
            ]
        ]


ifFirst : Int -> String -> String
ifFirst i string =
    if i == 0 then
        string

    else
        ""
