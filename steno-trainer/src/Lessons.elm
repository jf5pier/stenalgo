module Lessons exposing (Lesson, Lessons, Rule, Track, decoder, viewIntro, viewList)

{-| Lesson mode: the fixed learner progression exported by
`util/export_lessons.py` (`lessons.json`) -- tracks of lessons, each lesson
introducing new keys/chords with a French rule text and example words, then
drilling its own word pool through the same `Drill` engine as the Words mode.
Every learner-facing string (track and lesson titles, rule texts, examples)
comes from the JSON; only the navigation chrome is English, like the other
modes. The word records reuse the `practice-words.json` shape verbatim
(spec `docs/specs/lessons.md` §6), so `Drill.wordDecoder` decodes them
unchanged. Fetched only when the mode is first opened (see `Main.elm`).
-}

import Drill exposing (PracticeWord)
import Html exposing (Html, button, div, h2, h3, li, p, text, ul)
import Html.Attributes exposing (class, classList, disabled)
import Html.Events exposing (onClick)
import Json.Decode as D
import Json.Decode.Pipeline exposing (required)
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
    , examples : List String
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
        |> required "examples" (D.list D.string)


{-| The lesson picker: every track in export order with its title and
description, and that track's lessons as a vertical list of buttons (the
export's generation order is the learning order). `onSelect` receives the
lesson's id; `selected` (the id of the selected lesson, if any) only shows
up here after coming back from the intro or a drill. -}
viewList : (String -> msg) -> Maybe String -> Lessons -> Html msg
viewList onSelect selected lessons =
    div [ class "lessons" ]
        (List.map (viewTrack onSelect selected lessons) lessons.tracks)


viewTrack : (String -> msg) -> Maybe String -> Lessons -> Track -> Html msg
viewTrack onSelect selected lessons track =
    let
        trackLessons =
            List.filter (\lesson -> lesson.track == track.id) lessons.lessons
    in
    div [ class "lesson-track" ]
        [ h3 [] [ text track.title ]
        , p [ class "lesson-track-description" ] [ text track.description ]
        , ul [ class "lesson-list" ]
            (List.map (viewLessonButton onSelect selected) trackLessons)
        ]


viewLessonButton : (String -> msg) -> Maybe String -> Lesson -> Html msg
viewLessonButton onSelect selected lesson =
    li []
        [ button
            [ classList
                [ ( "lesson-item", True )
                , ( "selected", selected == Just lesson.id )
                ]
            , onClick (onSelect lesson.id)
            ]
            [ text lesson.title ]
        ]


{-| What a lesson introduces, before drilling it: its rules (the French text
and its example words), a keyboard rendering with the lesson's `newKeys` and
every key of its `newChords` lit, and the button that starts the drill
(handled in `Main.elm`, which shuffles the lesson's `words` into the shared
`Drill` engine). `keys` are the layout's keys already notation-mapped (see
`Notation.layout`); a lesson still loading its layout simply renders no
keyboard. Lessons with an empty pool (the affixes stub, a thin early phoneme
lesson) disable the button -- there is nothing to drill yet. -}
viewIntro :
    { onBack : msg
    , onStart : List PracticeWord -> msg
    , keys : List KeyInfo
    }
    -> Lesson
    -> Html msg
viewIntro config lesson =
    div [ class "lesson-intro" ]
        [ p [ class "lesson-back" ]
            [ button [ onClick config.onBack ] [ text "← Lessons" ] ]
        , p [ class "lesson-section-title" ] [ text lesson.sectionTitle ]
        , h2 [ class "lesson-title" ] [ text lesson.title ]
        , ul [ class "lesson-rules" ] (List.map viewRule lesson.rules)
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


{-| The rule texts embed their examples inline ("... (« rat », « rang »)"),
so the examples line is the compact reminder of the words to look for, not a
duplicate reading of the text. -}
viewRule : Rule -> Html msg
viewRule rule =
    li [ class "lesson-rule" ]
        ([ p [ class "lesson-rule-text" ] [ text rule.text ] ]
            ++ (if List.isEmpty rule.examples then
                    []

                else
                    [ p [ class "lesson-rule-examples" ]
                        [ text (String.join ", " rule.examples) ]
                    ]
               )
        )


{-| Every key the lesson introduces: its single keys plus every key of its
multi-key chords (a chord's keys belong to one keypress pressed together, so
they all light up at once). -}
highlightedKeys : Lesson -> Set Int
highlightedKeys lesson =
    lesson.newKeys ++ List.concat lesson.newChords |> Set.fromList
