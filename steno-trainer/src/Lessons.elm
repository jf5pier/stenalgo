module Lessons exposing (AffixData, Lesson, Lessons, Rule, Track, affixDecoder, decoder, mergeAffixData, viewIntro, viewList, viewPrevNext)

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

import Drill exposing (PracticeWord)
import Html exposing (Html, button, div, h2, h3, li, p, text, ul)
import Html.Attributes exposing (class, classList, disabled)
import Html.Events exposing (onClick)
import Json.Decode as D
import Json.Decode.Pipeline exposing (optional, required)
import Keyboard exposing (KeyInfo)
import Set exposing (Set)


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
    }


affixDecoder : D.Decoder AffixData
affixDecoder =
    D.map2 AffixData
        (D.field "rules" (D.list Keyboard.affixRuleDecoder))
        (D.field "lessons" (D.list lessonDecoder))


{-| The lessons with the `affixes` track's lessons (the stub) replaced by the
real ones, and that track's "à venir" description by a real one. An empty
list of affix lessons keeps the stub. -}
mergeAffixData : AffixData -> Lessons -> Lessons
mergeAffixData data lessons =
    if List.isEmpty data.lessons then
        lessons

    else
        { tracks =
            List.map
                (\track ->
                    if track.id == "affixes" then
                        { track | description = "Une règle d'abréviation par leçon : un contour court pour chaque mot, le long reste accepté." }

                    else
                        track
                )
                lessons.tracks
        , lessons = List.filter (\l -> l.track /= "affixes") lessons.lessons ++ data.lessons
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
            (List.map (viewLessonButton config) trackLessons)
        ]


viewLessonButton :
    { config | onSelect : String -> msg, selected : Maybe String, render : String -> String }
    -> Lesson
    -> Html msg
viewLessonButton config lesson =
    li []
        [ button
            [ classList
                [ ( "lesson-item", True )
                , ( "selected", config.selected == Just lesson.id )
                ]
            , onClick (config.onSelect lesson.id)
            ]
            [ text (config.render lesson.title) ]
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
        , h2 [ class "lesson-title" ] [ text (config.render lesson.title) ]
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
