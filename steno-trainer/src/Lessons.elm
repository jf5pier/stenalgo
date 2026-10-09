module Lessons exposing (Abbreviation, AffixData, ExpressionData, Lesson, Lessons, NumberData, PunctuationData, Rule, SpellingData, Track, affixDecoder, currentWords, decoder, displayTitle, expressionDecoder, mergeAffixData, mergeExpressionData, mergeNumberData, mergePunctuationData, mergeSpellingData, numberDecoder, numberEntries, pastWords, punctuationDecoder, punctuationEntries, spellingDecoder, spellingEntries, viewIntro, viewList, viewPrevNext)

{-| Lesson mode: the fixed learner progression exported by
`util/export_lessons.py` (`lessons.json`) -- tracks of lessons, each lesson
introducing new keys/chords with a French rule text and example words, then
drilling its own word pool through the same `Drill` engine as the Words mode.
Every learner-facing string (track and lesson titles, rule texts, the
examples embedded in them) comes from the JSON; only the navigation chrome
("Start drill", "← Lessons", "Previous/Next lesson") is English, like the
other modes. The word records reuse the `practice-words.json` shape verbatim
(spec `docs/specs/lessons.md` §6), so `Drill.wordDecoder` decodes them
unchanged. Fetched only when the mode is first opened (see `Main.elm`).
Rule texts, lesson/section/track titles and track descriptions embed
X-SAMPA (phoneme spans, key names, steno examples), so both views apply
the caller's `render` (notation -> string, `Notation.render`) to every
such string. Phoneme rules carry a `hand` group; the intro renders them
under the fixed French headers "Main gauche", "Les pouces", "Main droite"
(themselves free of every IPA-mapped character, spec §8), in that order,
skipping empty groups.
-}

import Definitions
import Drill exposing (PracticeWord)
import Html exposing (Html, button, div, h2, h3, li, p, text, ul)
import Html.Attributes exposing (class, classList, disabled)
import Html.Events exposing (onClick)
import Json.Decode as D
import Json.Decode.Pipeline exposing (custom, optional, required)
import Keyboard exposing (KeyInfo)
import Set exposing (Set)
import Style exposing (NumberStyle, Style(..))


type alias Track =
    { id : String
    , title : String
    , description : String
    }


type alias Rule =
    { kind : String
    , text : String
    , hand : Maybe String
    }


type alias Lesson =
    { id : String
    , track : String
    , index : Int
    , sectionTitle : String
    , title : String
    , kind : String
    , newKeys : List Int
    , newChords : List (List Int)
    , rules : List Rule
    , words : List PracticeWord
    }


type alias Lessons =
    { tracks : List Track
    , lessons : List Lesson
    }


decoder : D.Decoder Lessons
decoder =
    D.map2 Lessons
        (D.field "tracks" (D.list trackDecoder))
        (D.field "lessons" (D.list lessonDecoder))


{-| `affix-lessons.json` (`util/export_affix_lessons.py`): the affix rules and
the `affixes` track's lessons, which replace the stub lesson of `lessons.json`
(`mergeAffixData`). -}
type alias AffixData =
    { rules : List Keyboard.AffixRule
    , lessons : List Lesson
    , abbreviations : List Abbreviation
    }


{-| What the abbreviation hints need of an affix lesson's word: its spelling,
the rank of the rule that shortens it and its accepted outlines' steno text
(the short one first). -}
type alias Abbreviation =
    { ortho : String
    , rule : Int
    , outlines : List String
    }


affixDecoder : D.Decoder AffixData
affixDecoder =
    D.map3 AffixData
        (D.field "rules" (D.list Keyboard.affixRuleDecoder))
        (D.field "lessons" (D.list lessonDecoder))
        (D.field "lessons" (D.list (D.field "words" (D.list abbreviationDecoder))) |> D.map List.concat)


abbreviationDecoder : D.Decoder Abbreviation
abbreviationDecoder =
    D.map3 Abbreviation
        (D.field "ortho" D.string)
        (D.field "rule" D.int)
        (D.map2 (::)
            (D.field "steno" D.string)
            (D.oneOf [ D.field "alternates" (D.list (D.field "steno" D.string)), D.succeed [] ])
        )


{-| The lessons with the `affixes` track's lessons (the stub) replaced by the
real ones. An empty list of affix lessons keeps the stub. -}
mergeAffixData : AffixData -> Lessons -> Lessons
mergeAffixData data =
    replaceTrack "affixes" data.lessons


{-| `expression-lessons.json` (`util/export_expression_lessons.py`): the
expression abbreviation rules (the legend) and the `expressions` track's
lessons, which replace that track's stub lesson of `lessons.json`
(`mergeExpressionData`). The words of those lessons, and the sentences of
`expression-sentences.json`, name the rules they use by `ruleRanks`. -}
type alias ExpressionData =
    { rules : List Keyboard.ExpressionRule
    , lessons : List Lesson
    }


expressionDecoder : D.Decoder ExpressionData
expressionDecoder =
    D.map2 ExpressionData
        (D.field "rules" (D.list Keyboard.expressionRuleDecoder))
        (D.field "lessons" (D.list lessonDecoder))


{-| The lessons with the `expressions` track's lessons (the stub) replaced by
the real ones. An empty list keeps the stub. -}
mergeExpressionData : ExpressionData -> Lessons -> Lessons
mergeExpressionData data =
    replaceTrack "expressions" data.lessons


{-| `punctuation-lessons.json` (`util/export_punctuation_lessons.py`): the `ponctuation`
and `commandes` tracks, whose lessons exist once per chord style (same ids in both),
and the style's marks and commands for the Definitions page. -}
type alias PunctuationData =
    { tracks : List Track
    , plover : List Lesson
    , pluvier : List Lesson
    , ploverEntries : List Definitions.PunctuationEntry
    , pluvierEntries : List Definitions.PunctuationEntry
    }


punctuationDecoder : D.Decoder PunctuationData
punctuationDecoder =
    D.map5 PunctuationData
        (D.field "tracks" (D.list trackDecoder))
        (D.at [ "lessons", "plover" ] (D.list lessonDecoder))
        (D.at [ "lessons", "pluvier" ] (D.list lessonDecoder))
        (D.at [ "entries", "plover" ] (D.list Definitions.punctuationEntryDecoder))
        (D.at [ "entries", "pluvier" ] (D.list Definitions.punctuationEntryDecoder))


{-| The marks and commands of the chosen style, for the Definitions page. -}
punctuationEntries : Style -> PunctuationData -> List Definitions.PunctuationEntry
punctuationEntries style data =
    case style of
        Plover ->
            data.ploverEntries

        Pluvier ->
            data.pluvierEntries


{-| The lessons with the punctuation and command tracks of the chosen style: the
tracks are slipped in before the affixes track when they are not there yet, and
their lessons replaced by the style's, so switching style is a second merge. -}
mergePunctuationData : Style -> PunctuationData -> Lessons -> Lessons
mergePunctuationData style data lessons =
    let
        replacements =
            case style of
                Plover ->
                    data.plover

                Pluvier ->
                    data.pluvier

        withTracks =
            if List.any (\t -> List.any (\known -> known.id == t.id) lessons.tracks) data.tracks then
                lessons

            else
                { lessons | tracks = insertBeforeTrack [ "chiffres", "affixes" ] data.tracks lessons.tracks }
    in
    replaceTracks (List.map .id data.tracks) replacements withTracks


{-| `number-lessons.json` (`util/export_number_lessons.py`): the `chiffres` track,
whose lessons exist once per number theory AND per punctuation style (same ids in all
four: the glued comma and point of the decimal lesson are the punctuation style's), and
the theory's single-stroke numbers for the Definitions page. -}
type alias NumberData =
    { tracks : List Track
    , lapwingPlover : List Lesson
    , lapwingPluvier : List Lesson
    , pluvierPlover : List Lesson
    , pluvierPluvier : List Lesson
    , lapwingEntries : List Definitions.PunctuationEntry
    , pluvierEntries : List Definitions.PunctuationEntry
    }


numberDecoder : D.Decoder NumberData
numberDecoder =
    D.succeed NumberData
        |> required "tracks" (D.list trackDecoder)
        |> custom (D.at [ "lessons", "lapwing", "plover" ] (D.list lessonDecoder))
        |> custom (D.at [ "lessons", "lapwing", "pluvier" ] (D.list lessonDecoder))
        |> custom (D.at [ "lessons", "pluvier", "plover" ] (D.list lessonDecoder))
        |> custom (D.at [ "lessons", "pluvier", "pluvier" ] (D.list lessonDecoder))
        |> custom (D.at [ "entries", "lapwing" ] (D.list Definitions.punctuationEntryDecoder))
        |> custom (D.at [ "entries", "pluvier" ] (D.list Definitions.punctuationEntryDecoder))


{-| The single-stroke numbers of the chosen theory, for the Definitions page. -}
numberEntries : NumberStyle -> NumberData -> List Definitions.PunctuationEntry
numberEntries style data =
    case style of
        Style.Lapwing ->
            data.lapwingEntries

        Style.PluvierNumbers ->
            data.pluvierEntries


{-| The lessons with the `chiffres` track of the chosen number theory and punctuation
style, slipped in before the affixes track when it is not there yet (after the
punctuation tracks, which are inserted before it too), its lessons replaced on a switch. -}
mergeNumberData : NumberStyle -> Style -> NumberData -> Lessons -> Lessons
mergeNumberData numberStyle style data lessons =
    let
        replacements =
            case ( numberStyle, style ) of
                ( Style.Lapwing, Plover ) ->
                    data.lapwingPlover

                ( Style.Lapwing, Pluvier ) ->
                    data.lapwingPluvier

                ( Style.PluvierNumbers, Plover ) ->
                    data.pluvierPlover

                ( Style.PluvierNumbers, Pluvier ) ->
                    data.pluvierPluvier

        withTracks =
            if List.any (\t -> List.any (\known -> known.id == t.id) lessons.tracks) data.tracks then
                lessons

            else
                { lessons | tracks = insertBeforeTrack [ "affixes" ] data.tracks lessons.tracks }
    in
    replaceTracks (List.map .id data.tracks) replacements withTracks


{-| `spelling-lessons.json` (`util/export_spelling_lessons.py`): the `epellation` track
of the one spelling theory (no style: a single lesson list) and its 156 letter strokes
for the Definitions page. -}
type alias SpellingData =
    { tracks : List Track
    , lessons : List Lesson
    , entries : List Definitions.PunctuationEntry
    }


spellingDecoder : D.Decoder SpellingData
spellingDecoder =
    D.map3 SpellingData
        (D.field "tracks" (D.list trackDecoder))
        (D.field "lessons" (D.list lessonDecoder))
        (D.field "entries" (D.list Definitions.punctuationEntryDecoder))


spellingEntries : SpellingData -> List Definitions.PunctuationEntry
spellingEntries data =
    data.entries


{-| The lessons with the `epellation` track, slipped in before the affixes track
when it is not there yet (after the punctuation and number tracks, inserted before it too). -}
mergeSpellingData : SpellingData -> Lessons -> Lessons
mergeSpellingData data lessons =
    let
        withTracks =
            if List.any (\t -> List.any (\known -> known.id == t.id) lessons.tracks) data.tracks then
                lessons

            else
                { lessons | tracks = insertBeforeTrack [ "affixes" ] data.tracks lessons.tracks }
    in
    replaceTracks (List.map .id data.tracks) data.lessons withTracks


insertBeforeTrack : List String -> List Track -> List Track -> List Track
insertBeforeTrack ids new tracks =
    case tracks of
        [] ->
            new

        track :: rest ->
            if List.member track.id ids then
                new ++ tracks

            else
                track :: insertBeforeTrack ids new rest


{-| Replace the stub (or any earlier lessons) of one track by `replacements`,
then put every lesson back in track order (the `tracks` list, then the lesson's
`index`), so the order does not depend on which optional file arrived first.
No replacements: the lessons stay as they are. -}
replaceTrack : String -> List Lesson -> Lessons -> Lessons
replaceTrack track replacements =
    replaceTracks [ track ] replacements


replaceTracks : List String -> List Lesson -> Lessons -> Lessons
replaceTracks replacedTracks replacements lessons =
    if List.isEmpty replacements then
        lessons

    else
        let
            trackPosition id =
                lessons.tracks
                    |> List.indexedMap Tuple.pair
                    |> List.filter (\( _, t ) -> t.id == id)
                    |> List.head
                    |> Maybe.map Tuple.first
                    |> Maybe.withDefault (List.length lessons.tracks)
        in
        { lessons
            | lessons =
                (List.filter (\l -> not (List.member l.track replacedTracks)) lessons.lessons ++ replacements)
                    |> List.sortBy (\l -> ( trackPosition l.track, l.index ))
        }


trackDecoder : D.Decoder Track
trackDecoder =
    D.succeed Track
        |> required "id" D.string
        |> required "title" D.string
        |> required "description" D.string


lessonDecoder : D.Decoder Lesson
lessonDecoder =
    D.succeed Lesson
        |> required "id" D.string
        |> required "track" D.string
        |> required "index" D.int
        |> required "sectionTitle" D.string
        |> required "title" D.string
        |> required "kind" D.string
        |> required "newKeys" (D.list D.int)
        |> required "newChords" (D.list (D.list D.int))
        |> required "rules" (D.list ruleDecoder)
        |> required "words" (D.list Drill.wordDecoder)


ruleDecoder : D.Decoder Rule
ruleDecoder =
    D.succeed Rule
        |> required "kind" D.string
        |> required "text" D.string
        |> optional "hand" (D.nullable D.string) Nothing


{-| The hand groups of the intro's rule grouping, in display order: left
non-thumb fingers, then the thumbs of both sides, then right non-thumb
fingers. The labels are fixed French strings -- no IPA-mapped character
(the IPA toggle rewrites whole rendered strings, spec §8). -}
handGroups : List ( String, String )
handGroups =
    [ ( "left", "Main gauche" ), ( "thumbs", "Les pouces" ), ( "right", "Main droite" ) ]


{-| The lesson picker: every track in export order with its title and
description, and that track's lessons as a vertical list of buttons (the
export's generation order is the learning order). `onSelect` receives the
lesson's id; `selected` (the id of the selected lesson, if any) only shows
up here after coming back from the intro or a drill. `render` (the
notation's string rewriter, `Notation.render`) is applied to the track and
lesson titles and the track descriptions, whose X-SAMPA content must follow
the notation toggle. -}
viewList :
    { onSelect : String -> msg
    , selected : Maybe String
    , render : String -> String
    }
    -> Lessons
    -> Html msg
viewList config lessons =
    div [ class "lessons" ]
        (List.map (viewTrack config lessons) lessons.tracks)


viewTrack :
    { config | onSelect : String -> msg, selected : Maybe String, render : String -> String }
    -> Lessons
    -> Track
    -> Html msg
viewTrack config lessons track =
    let
        trackLessons =
            List.filter (\lesson -> lesson.track == track.id) lessons.lessons
    in
    div [ class "lesson-track" ]
        [ h3 [] [ text (config.render track.title) ]
        , p [ class "lesson-track-description" ] [ text (config.render track.description) ]
        , ul [ class "lesson-list" ]
            (List.map (\lesson -> viewLessonButton config (displayTitle config.render lessons lesson) lesson) trackLessons)
        ]


viewLessonButton :
    { config | onSelect : String -> msg, selected : Maybe String, render : String -> String }
    -> String
    -> Lesson
    -> Html msg
viewLessonButton config title lesson =
    li []
        [ button
            [ classList
                [ ( "lesson-item", True )
                , ( "selected", config.selected == Just lesson.id )
                ]
            , onClick (config.onSelect lesson.id)
            ]
            [ text title ]
        ]


{-| What a lesson introduces, before drilling it: its rules (the French text,
examples embedded inline per phoneme), a keyboard rendering with the lesson's
`newKeys` and every key of its `newChords` lit, and the button that starts the
drill (handled in `Main.elm`, which shuffles the lesson's `words` into the
shared `Drill` engine). `onPrev`/`onNext` step through the global lesson order
(`viewPrevNext`); `Nothing` disables the button at the two ends. `keys` are
the layout's keys already notation-mapped (see `Notation.layout`); a lesson
still loading its layout simply renders no keyboard. `render` (the notation's
string rewriter, `Notation.render`) is applied to the section title, the
lesson title and every rule text -- their X-SAMPA content must follow the
notation toggle. Lessons with an empty pool (the affixes stub, a thin early
phoneme lesson) disable the drill button -- there is nothing to drill yet. -}
viewIntro :
    { onBack : msg
    , onStart : List PracticeWord -> msg
    , onPrev : Maybe msg
    , onNext : Maybe msg
    , render : String -> String
    , keys : List KeyInfo
    , title : String
    }
    -> Lesson
    -> Html msg
viewIntro config lesson =
    div [ class "lesson-intro" ]
        [ p [ class "lesson-back" ]
            ([ button [ onClick config.onBack ] [ text "← Lessons" ] ]
                ++ viewPrevNext config.onPrev config.onNext
            )
        , p [ class "lesson-section-title" ] [ text (config.render lesson.sectionTitle) ]
        , h2 [ class "lesson-title" ] [ text config.title ]
        , viewRules config.render lesson.rules
        , div [ class "lesson-keyboard" ]
            [ Keyboard.view
                { highlighted = highlightedKeys lesson
                , correct = Nothing
                }
                config.keys
            ]
        , p [ class "lesson-start" ]
            [ button
                [ onClick (config.onStart lesson.words)
                , disabled (List.isEmpty lesson.words)
                ]
                [ text "Start drill" ]
            ]
        ]


{-| The lesson's rules: phoneme rules (those carrying a `hand` group) render
grouped under the three hand headers in handGroups order, skipping empty
groups and keeping each group's internal order as exported; rules without a
hand (the marker tracks) render as a plain list. -}
viewRules : (String -> String) -> List Rule -> Html msg
viewRules render rules =
    if List.all (\rule -> rule.hand == Nothing) rules then
        ul [ class "lesson-rules" ] (List.map (viewRule render) rules)

    else
        div [ class "lesson-rules" ]
            (List.filterMap (viewHandGroup render rules) handGroups)


viewHandGroup :
    (String -> String)
    -> List Rule
    -> ( String, String )
    -> Maybe (Html msg)
viewHandGroup render rules ( hand, label ) =
    let
        handRules =
            List.filter (\rule -> rule.hand == Just hand) rules
    in
    if List.isEmpty handRules then
        Nothing

    else
        Just <|
            div [ class "lesson-hand-group" ]
                [ h3 [ class "lesson-hand-title" ] [ text (label ++ " :") ]
                , ul [ class "lesson-hand-rules" ]
                    (List.map (viewRule render) handRules)
                ]


{-| One rule line: the French text with its examples already embedded by the
exporter. `render` rewrites the text's X-SAMPA (phoneme spans, key names,
steno examples) per the notation toggle. -}
viewRule : (String -> String) -> Rule -> Html msg
viewRule render rule =
    li [ class "lesson-rule" ]
        [ p [ class "lesson-rule-text" ] [ text (render rule.text) ] ]


{-| The "Previous lesson"/"Next lesson" pair (English chrome, like "Start
drill"): `Nothing` disables the button -- never hides it -- at the two ends
of the global lesson order. Shared by the intro and the drill page; both
navigate to the target lesson's intro, handled in `Main.elm`. -}
viewPrevNext : Maybe msg -> Maybe msg -> List (Html msg)
viewPrevNext onPrev onNext =
    [ navButton "← Previous lesson" onPrev
    , text " "
    , navButton "Next lesson →" onNext
    ]


navButton : String -> Maybe msg -> Html msg
navButton label maybeMsg =
    case maybeMsg of
        Just msg ->
            button [ class "lesson-nav-button", onClick msg ] [ text label ]

        Nothing ->
            button [ class "lesson-nav-button", disabled True ] [ text label ]


{-| Every key the lesson introduces: its single keys plus every key of its
multi-key chords (a chord's keys belong to one keypress pressed together, so
they all light up at once). -}
highlightedKeys : Lesson -> Set Int
highlightedKeys lesson =
    lesson.newKeys ++ List.concat lesson.newChords |> Set.fromList


{-| The lesson's title with its number counted over ALL the lessons in
export order, so the numbering carries on from one track to the next instead of
restarting at 1 in each (the exported titles number within their track, in
words). The number is a digit string put in AFTER `render` (the notation's
rewriter would turn a "1" into an IPA glyph); only the rest of the title goes
through it. -}
displayTitle : (String -> String) -> Lessons -> Lesson -> String
displayTitle render lessons lesson =
    let
        position =
            lessons.lessons
                |> List.indexedMap Tuple.pair
                |> List.filter (\( _, l ) -> l.id == lesson.id)
                |> List.head
                |> Maybe.map (\( i, _ ) -> i + 1)
                |> Maybe.withDefault 1
    in
    case String.split " : " lesson.title of
        _ :: (_ :: _ as rest) ->
            "Le\u{00E7}on " ++ String.fromInt position ++ " : " ++ render (String.join " : " rest)

        _ ->
            render lesson.title


{-| The words a lesson drills by default: those that use something the lesson
introduces (a stroke holding all the keys of one of its new chords, else a stroke
with one of its new keys), the earlier keys being used as needed to complete
them. A phoneme lesson's pool is already the words it unlocks (spec §2.6), so it
drills all of it. A lesson introducing nothing of its own (the tense lessons) drills its
whole pool, as does one where nothing matches. -}
currentWords : Lesson -> List PracticeWord
currentWords lesson =
    let
        usesNew word =
            if List.isEmpty lesson.newChords then
                List.any (\stroke -> List.any (\k -> List.member k lesson.newKeys) stroke) word.strokes

            else
                List.any
                    (\stroke -> List.any (\chord -> List.all (\k -> List.member k stroke) chord) lesson.newChords)
                    word.strokes

        chosen =
            if lesson.track == "phonemes" || (List.isEmpty lesson.newKeys && List.isEmpty lesson.newChords) then
                -- a phoneme lesson's pool is already the words it unlocks
                lesson.words

            else
                List.filter usesNew lesson.words
    in
    if List.isEmpty chosen then
        lesson.words

    else
        chosen


{-| The words of the earlier lessons of the same track (in order, without
repeats): the "past" half of the 50/50 drill. -}
pastWords : Lessons -> Lesson -> List PracticeWord
pastWords lessons lesson =
    lessons.lessons
        |> List.filter (\l -> l.track == lesson.track && l.index < lesson.index)
        |> List.concatMap .words
        |> List.foldl
            (\word ( seen, acc ) ->
                let
                    key =
                        word.ortho ++ "|" ++ word.steno
                in
                if Set.member key seen then
                    ( seen, acc )

                else
                    ( Set.insert key seen, word :: acc )
            )
            ( Set.empty, [] )
        |> Tuple.second
        |> List.reverse
