module Definitions exposing (Definitions, ExpressionDefinitions, PunctuationEntry, chordsOfSpelling, decoder, emptyExpressions, expressionsDecoder, punctuationEntryDecoder, view)

{-| Definition mode: type a spelling, get every word sharing a base chord
with it -- its homophones, the words the conjugation marks and the `*`/`#`
track have to tell apart -- each with its reading(s), pronunciation and final
chord(s). Data from `util/export_definitions.py` (`definitions.json`),
which covers the whole lexicon, so it's only fetched when this mode is first
opened.
-}

import Array exposing (Array)
import Dict exposing (Dict)
import Html exposing (Html, button, h3, p, span, table, tbody, td, text, th, thead, tr)
import Html.Attributes exposing (class, classList, title, type_)
import Html.Events exposing (onClick)
import Json.Decode as D
import Set
import Style exposing (NumberStyle)


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


{-| A composed phrase (`de la`) and what the expression layer writes for it: the
abbreviated outline, the plain one, and the saving. `phonology` is the phrase's
(raw X-SAMPA) one, for the phoneme boards of the keyboard simulation. -}
type alias Phrase =
    { text : String
    , phonology : String
    , steno : String
    , longform : String
    , label : String
    }


{-| An attach rule: the particle (`de`, `n' y`) written as a keypress, `steno`
being that keypress alone, with its frequent phrases as examples. -}
type alias Attach =
    { text : String
    , position : String
    , label : String
    , keyNames : List String
    , steno : String
    , phonology : String
    , examples : List Phrase
    }


{-| `expression-definitions.json` (`util/export_expression_definitions.py`). -}
type alias ExpressionDefinitions =
    { attaches : List Attach
    , phrases : List Phrase
    }


{-| One punctuation mark or command of the active style (`punctuation-lessons.json`,
`util/export_punctuation_lessons.py`): its name, glyph, every chord (the `primary`
first, then the other spellings -- `*`/`#` twins, the other style's chord) and what
typing it outputs. -}
type alias PunctuationEntry =
    { name : String
    , glyph : String
    , family : String
    , primary : String
    , chords : List String
    , output : String
    , keywords : List String -- other characters that find it (the straight " finds the guillemets)
    }


punctuationEntryDecoder : D.Decoder PunctuationEntry
punctuationEntryDecoder =
    D.map7 PunctuationEntry
        (D.field "name" D.string)
        (D.field "glyph" D.string)
        (D.field "family" D.string)
        (D.field "primary" D.string)
        (D.field "chords" (D.list D.string))
        (D.field "output" D.string)
        (D.oneOf [ D.field "keywords" (D.list D.string), D.succeed [] ])


emptyExpressions : ExpressionDefinitions
emptyExpressions =
    { attaches = [], phrases = [] }


expressionsDecoder : D.Decoder ExpressionDefinitions
expressionsDecoder =
    let
        phrase =
            D.map5 Phrase
                (D.field "text" D.string)
                (D.field "phonology" D.string)
                (D.field "steno" D.string)
                (D.field "longform" D.string)
                (D.field "label" D.string)

        attach =
            D.map7 Attach
                (D.field "text" D.string)
                (D.field "position" D.string)
                (D.field "label" D.string)
                (D.field "keyNames" (D.list D.string))
                (D.field "steno" D.string)
                (D.field "phonology" D.string)
                (D.field "examples" (D.list phrase))
    in
    D.map2 ExpressionDefinitions
        (D.field "attaches" (D.list attach))
        (D.field "phrases" (D.list phrase))


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
which needs its marks just the same. Every chord and abbreviation is a button
that sends `onChord` the word's phonology and its steno text (the page simulates it on the keyboard).
-}
view : (String -> String) -> (String -> String -> msg) -> Dict String (Dict String String) -> ExpressionDefinitions -> List PunctuationEntry -> NumberStyle -> String -> Definitions -> Html msg
view render onChord abbreviations expressions punctuation numberStyle query definitions =
    let
        spelling =
            String.toLower (String.join " " (String.words (String.replace "\u{2019}" "'" query)))

        attaches =
            List.filter (\a -> a.text == spelling) expressions.attaches

        phrases =
            List.filter (\ph -> ph.text == spelling) expressions.phrases

        marks =
            punctuationMatches query (List.filter (\entry -> entry.family /= "chiffres") punctuation)
                ++ numberResult numberStyle punctuation query

        groups =
            Dict.get spelling definitions.groupsByOrtho
                |> Maybe.withDefault []
                |> List.reverse
                |> List.filterMap (\index -> Array.get index definitions.groups)
    in
    if String.isEmpty spelling then
        p [ class "definition-hint" ] [ text "Type a word's spelling to see its homophones, readings and chords." ]

    else if List.isEmpty groups && List.isEmpty attaches && List.isEmpty phrases && List.isEmpty marks then
        p [ class "definition-hint" ] [ text ("No word spelled \u{201C}" ++ spelling ++ "\u{201D} in the dictionary.") ]

    else
        Html.div []
            (List.map (viewGroup render onChord abbreviations spelling) groups
                ++ List.map (viewAttach render onChord) attaches
                ++ List.map (viewPhrase render onChord) phrases
                ++ viewPunctuation render onChord marks
            )


{-| The number the query spells (digits only), resolved to its strokes in the chosen theory:
one stroke when it fits (`123` on the bar), several otherwise (`21` is `2` then `1`), joined
by `/`. Only that number is shown, not the other numbers that contain it. -}
numberResult : NumberStyle -> List PunctuationEntry -> String -> List PunctuationEntry
numberResult numberStyle entries query =
    let
        digits =
            String.trim query

        strokeOf =
            entries
                |> List.filter (\entry -> entry.family == "chiffres")
                |> List.map (\entry -> ( entry.glyph, entry.primary ))
                |> Dict.fromList

        pieces =
            case numberStyle of
                Style.Lapwing ->
                    splitLapwing digits

                Style.PluvierNumbers ->
                    splitBar digits

        chords =
            List.filterMap (\piece -> Dict.get piece strokeOf) pieces
    in
    if String.isEmpty digits || not (String.all Char.isDigit digits) || List.length chords /= List.length pieces then
        []

    else
        [ { name = "le nombre " ++ digits
          , glyph = digits
          , family = "chiffres"
          , primary = String.join "/" chords
          , chords = [ String.join "/" chords ]
          , output = digits
          , keywords = []
          }
        ]


{-| Pluvier's number bar: runs of digits that go up in the keyboard order 1 2 3 4 5 0 6 7 8 9
are one stroke each (`util/number_lessons.py`). -}
splitBar : String -> List String
splitBar digits =
    let
        rank c =
            String.indexes (String.fromChar c) "1234506789" |> List.head |> Maybe.withDefault 0

        step c runs =
            case runs of
                run :: rest ->
                    if rank c > (String.right 1 run |> String.toList |> List.head |> Maybe.map rank |> Maybe.withDefault 0) then
                        (run ++ String.fromChar c) :: rest

                    else
                        String.fromChar c :: runs

                [] ->
                    [ String.fromChar c ]
    in
    String.toList digits |> List.foldl step [] |> List.reverse


{-| Lapwing's numpad: a digit with the (up to three) zeros that follow it is one stroke, and
zeros with no digit before them up to three. -}
splitLapwing : String -> List String
splitLapwing digits =
    case String.uncons digits of
        Nothing ->
            []

        Just ( first, rest ) ->
            let
                most =
                    if first == '0' then
                        2

                    else
                        3

                zeros =
                    rest |> String.toList |> takeWhileZero |> List.take most |> List.length
            in
            (String.fromChar first ++ String.repeat zeros "0") :: splitLapwing (String.dropLeft zeros rest)


takeWhileZero : List Char -> List Char
takeWhileZero chars =
    case chars of
        '0' :: more ->
            '0' :: takeWhileZero more

        _ ->
            []


{-| The punctuation marks and commands the query names: its glyph or one of its
chords exactly, or (from three letters on) a part of its name. -}
punctuationMatches : String -> List PunctuationEntry -> List PunctuationEntry
punctuationMatches query entries =
    let
        raw =
            String.trim query

        lowered =
            String.toLower raw
    in
    if String.isEmpty raw then
        []

    else
        entries
            |> List.filter
                (\entry ->
                    entry.glyph == raw
                        || List.member raw entry.keywords
                        || List.member raw entry.chords
                        || (String.length lowered >= 3 && String.contains lowered (String.toLower entry.name))
                )


viewPunctuation : (String -> String) -> (String -> String -> msg) -> List PunctuationEntry -> List (Html msg)
viewPunctuation render onChord entries =
    if List.isEmpty entries then
        []

    else
        [ Html.div [ class "definition-group" ]
            [ h3 [] [ text "Punctuation and commands" ]
            , table [ class "definition-table" ]
                [ thead [] [ tr [] [ th [] [ text "Name" ], th [] [ text "Mark" ], th [] [ text "Chords" ], th [] [ text "Types" ] ] ]
                , tbody []
                    (List.map
                        (\entry ->
                            tr [ class "searched" ]
                                [ td [] [ text entry.name ]
                                , td [] [ text entry.glyph ]
                                , td [ class "definition-steno" ]
                                    (List.map (chordButton render (onChord "")) entry.chords |> List.intersperse (text " "))
                                , td [] [ text (visibleSpaces entry.output) ]
                                ]
                        )
                        entries
                    )
                ]
            ]
        ]


{-| A typed result with its no-break spaces and newlines made visible. -}
visibleSpaces : String -> String
visibleSpaces output =
    output
        |> String.replace "\u{00A0}" "\u{2423}"
        |> String.replace "\n" "\u{21B5}"


viewGroup : (String -> String) -> (String -> String -> msg) -> Dict String (Dict String String) -> String -> Group -> Html msg
viewGroup render onChord abbreviations spelling group =
    let
        abbreviationOf entry chord =
            Dict.get entry.ortho abbreviations
                |> Maybe.andThen (Dict.get chord.steno)

        hasAbbreviations =
            List.any (\entry -> List.any (\chord -> abbreviationOf entry chord /= Nothing) entry.chords) group.entries

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
                        ([ td [] [ text (ifFirst i entry.ortho) ]
                         , td [] [ text (ifFirst i ("/" ++ render entry.phonology ++ "/")) ]
                         , td [ class "definition-steno" ] [ chordButton render (onChord entry.phonology) chord.steno ]
                         , td [] [ text chord.label ]
                         ]
                            ++ (if hasAbbreviations then
                                    [ td [ class "definition-steno" ] [ abbreviationOf entry chord |> Maybe.map (chordButton render (onChord entry.phonology)) |> Maybe.withDefault (text "") ] ]

                                else
                                    []
                               )
                        )
                )
                entry.chords
    in
    Html.div [ class "definition-group" ]
        [ h3 [] [ text ("Base chord " ++ render group.base) ]
        , table [ class "definition-table" ]
            [ thead []
                [ tr []
                    ([ th [] [ text "Word" ], th [] [ text "Pronunciation" ], th [] [ text "Chord" ], th [] [ text "Reading" ] ]
                        ++ (if hasAbbreviations then
                                [ th [] [ text "Abbrev." ] ]

                            else
                                []
                           )
                    )
                ]
            , tbody [] (List.concatMap entryRows group.entries)
            ]
        ]


viewAttach : (String -> String) -> (String -> String -> msg) -> Attach -> Html msg
viewAttach render onChord attach =
    Html.div [ class "definition-group" ]
        [ h3 [] [ text ("Attach word \u{00AB} " ++ attach.text ++ " \u{00BB}") ]
        , p [ class "definition-hint" ] [ text attach.label ]
        , table [ class "definition-table" ]
            [ thead [] [ tr [] [ th [] [ text "Keypress" ], th [] [ text "Keys" ] ] ]
            , tbody []
                [ tr []
                    [ td [ class "definition-steno" ] [ chordButton render (onChord attach.phonology) attach.steno ]
                    , td [] [ text (String.join " " attach.keyNames) ]
                    ]
                ]
            ]
        , if List.isEmpty attach.examples then
            text ""

          else
            table [ class "definition-table" ]
                [ thead [] [ tr [] [ th [] [ text "Example" ], th [] [ text "Long form" ], th [] [ text "Abbreviated" ], th [] [ text "" ] ] ]
                , tbody [] (List.map (phraseRow render onChord) attach.examples)
                ]
        ]


viewPhrase : (String -> String) -> (String -> String -> msg) -> Phrase -> Html msg
viewPhrase render onChord phrase =
    Html.div [ class "definition-group" ]
        [ h3 [] [ text ("Composed attach words \u{00AB} " ++ phrase.text ++ " \u{00BB}") ]
        , table [ class "definition-table" ]
            [ thead [] [ tr [] [ th [] [ text "Phrase" ], th [] [ text "Long form" ], th [] [ text "Abbreviated" ], th [] [ text "" ] ] ]
            , tbody [] [ phraseRow render onChord phrase ]
            ]
        ]


phraseRow : (String -> String) -> (String -> String -> msg) -> Phrase -> Html msg
phraseRow render onChord phrase =
    tr [ class "searched" ]
        [ td [] [ text phrase.text ]
        , td [ class "definition-steno" ] [ chordButton render (onChord phrase.phonology) phrase.longform ]
        , td [ class "definition-steno" ] [ chordButton render (onChord phrase.phonology) phrase.steno ]
        , td [] [ span [ class "definition-hint" ] [ text phrase.label ] ]
        ]


chordButton : (String -> String) -> (String -> msg) -> String -> Html msg
chordButton render onChord steno =
    button [ type_ "button", class "chord-button", title "Show on the keyboard", onClick (onChord steno) ] [ text (render steno) ]


ifFirst : Int -> String -> String
ifFirst i string =
    if i == 0 then
        string

    else
        ""


{-| Reverse lookup: every chord (steno text, possibly several strokes joined by `/`)
that writes the exact spelling, most frequent entry first, without duplicates. -}
chordsOfSpelling : Definitions -> String -> List String
chordsOfSpelling definitions spelling =
    Dict.get spelling definitions.groupsByOrtho
        |> Maybe.withDefault []
        |> List.reverse
        |> List.filterMap (\index -> Array.get index definitions.groups)
        |> List.concatMap .entries
        |> List.filter (\entry -> entry.ortho == spelling)
        |> List.concatMap .chords
        |> List.map .steno
        |> List.foldl
            (\steno seen ->
                if List.member steno seen then
                    seen

                else
                    seen ++ [ steno ]
            )
            []
