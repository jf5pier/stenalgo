module Main exposing (main)

import Browser
import Definitions exposing (Definitions)
import Dict exposing (Dict)
import Drill exposing (PracticeWord)
import GeminiPr
import Html exposing (Html, button, div, h1, input, p, text)
import Html.Attributes exposing (autofocus, class, disabled, placeholder, type_, value)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode as D
import Keyboard exposing (KeyInfo, Layout)
import Lessons exposing (Lessons)
import Notation exposing (Notation)
import Ports
import Random
import Set


type LoadState a
    = Loading
    | Loaded a
    | Failed String


{-| Words drill single words (`practice-words.json`); sentences drill short
common sentences word by word (`practice-sentences.json`, see
`util/export_practice_sentences.py`). Both run through the same `Drill`
state machine -- a sentence is just one long multi-stroke item. Definitions
is a lookup, not a drill: type a spelling, see its homophones (see
`Definitions`). Lessons is the fixed progression of `lessons.json`: pick a
lesson, read its rules, then drill its own word pool through the same `Drill`
engine (see `Lessons`). -}
type Mode
    = WordMode
    | SentenceMode
    | DefinitionMode
    | LessonMode


{-| The strokes correctly typed so far for the current target word (a
sentence's current word), as steno text, shown in place of the chord when
hints are off. `complete` once the word's last stroke is in: it stays on
screen (the drill has already moved on) until the next word's first stroke. -}
type alias TypedStrokes =
    { strokes : List String
    , complete : Bool
    }


type SerialStatus
    = CheckingSupport
    | Unsupported
    | Disconnected
    | Connected


type alias Model =
    { layout : LoadState Layout
    , words : LoadState (List PracticeWord)
    , sentences : LoadState (List PracticeWord)
    , mode : Mode
    , drill : Maybe Drill.State
    , keymap : Dict String Int
    , serial : SerialStatus
    , notation : Notation
    , definitions : Maybe (LoadState Definitions)
    , lessons : Maybe (LoadState Lessons)
    , affixData : Maybe Lessons.AffixData -- affix-lessons.json, when it came back (the stub stays otherwise)
    , selectedLesson : Maybe String
    , query : String
    , hints : Bool
    , lastStroke : Set.Set Int
    , typed : TypedStrokes
    }


type Msg
    = GotLayout (Result Http.Error Layout)
    | GotWords (Result Http.Error (List PracticeWord))
    | GotSentences (Result Http.Error (List PracticeWord))
    | SwitchMode Mode
    | ShuffledWords (List PracticeWord)
    | ClickConnect
    | SerialStatusChanged String
    | IncomingBytes (List Int)
    | ToggleNotation
    | GotDefinitions (Result Http.Error Definitions)
    | GotLessons (Result Http.Error Lessons)
    | GotAffixData (Result Http.Error Lessons.AffixData)
    | SelectLesson String
    | PrevLesson
    | NextLesson
    | BackToLessonList
    | StartLessonDrill (List PracticeWord)
    | QueryChanged String
    | ToggleHints


main : Program () Model Msg
main =
    Browser.element { init = init, update = update, subscriptions = subscriptions, view = view }


init : () -> ( Model, Cmd Msg )
init _ =
    ( { layout = Loading
      , words = Loading
      , sentences = Loading
      , mode = WordMode
      , drill = Nothing
      , keymap = Dict.empty
      , serial = CheckingSupport
      , notation = Notation.XSampa
      , definitions = Nothing
      , lessons = Nothing
      , affixData = Nothing
      , selectedLesson = Nothing
      , query = ""
      , hints = True
      , lastStroke = Set.empty
      , typed = noTypedStrokes
      }
    , Cmd.batch
        [ Http.get { url = "public/data/keyboard-layout.json", expect = Http.expectJson GotLayout Keyboard.decoder }
        , Http.get { url = "public/data/practice-words.json", expect = Http.expectJson GotWords Drill.decoder }
        , Http.get { url = "public/data/practice-sentences.json", expect = Http.expectJson GotSentences Drill.sentenceDecoder }
        ]
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GotLayout (Ok layout) ->
            ( { model | layout = Loaded layout, keymap = Keyboard.geminiKeymap layout.keys }, Cmd.none )

        GotLayout (Err err) ->
            ( { model | layout = Failed (httpErrorToString err) }, Cmd.none )

        GotWords (Ok words) ->
            startDrillIfIdle { model | words = Loaded words }

        GotWords (Err err) ->
            ( { model | words = Failed (httpErrorToString err) }, Cmd.none )

        GotSentences (Ok sentences) ->
            startDrillIfIdle { model | sentences = Loaded sentences }

        GotSentences (Err err) ->
            ( { model | sentences = Failed (httpErrorToString err) }, Cmd.none )

        SwitchMode mode ->
            if mode == model.mode then
                ( model, Cmd.none )

            else if mode == DefinitionMode && model.definitions == Nothing then
                ( { model | mode = mode, drill = Nothing, typed = noTypedStrokes, definitions = Just Loading }
                , Http.get { url = "public/data/definitions.json", expect = Http.expectJson GotDefinitions Definitions.decoder }
                )

            else if mode == LessonMode && model.lessons == Nothing then
                ( { model | mode = mode, drill = Nothing, typed = noTypedStrokes, selectedLesson = Nothing, lessons = Just Loading }
                , Cmd.batch
                    [ Http.get { url = "public/data/lessons.json", expect = Http.expectJson GotLessons Lessons.decoder }
                    , Http.get { url = "public/data/affix-lessons.json", expect = Http.expectJson GotAffixData Lessons.affixDecoder }
                    ]
                )

            else if mode == LessonMode then
                -- Already fetched (or fetching): back to the picker, not an
                -- auto-resume of whatever lesson was last selected. No drill
                -- starts (nothing is selected), so no `startDrillIfIdle`.
                ( { model | mode = mode, drill = Nothing, typed = noTypedStrokes, selectedLesson = Nothing }
                , Cmd.none
                )

            else
                startDrillIfIdle { model | mode = mode, drill = Nothing, typed = noTypedStrokes }

        GotDefinitions (Ok definitions) ->
            ( { model | definitions = Just (Loaded definitions) }, Cmd.none )

        GotDefinitions (Err err) ->
            ( { model | definitions = Just (Failed (httpErrorToString err)) }, Cmd.none )

        GotLessons (Ok lessons) ->
            ( { model | lessons = Just (Loaded (mergeAffix model.affixData lessons)) }, Cmd.none )

        GotAffixData (Ok data) ->
            -- Whichever of lessons.json / affix-lessons.json arrives last does the merge.
            ( { model
                | affixData = Just data
                , lessons =
                    case model.lessons of
                        Just (Loaded lessons) ->
                            Just (Loaded (Lessons.mergeAffixData data lessons))

                        other ->
                            other
              }
            , Cmd.none
            )

        GotAffixData (Err _) ->
            -- Optional layer: without the file the affixes track keeps its stub lesson.
            ( model, Cmd.none )

        GotLessons (Err err) ->
            ( { model | lessons = Just (Failed (httpErrorToString err)) }, Cmd.none )

        SelectLesson id ->
            -- Picking a lesson shows its intro; its drill only starts on the
            -- intro's explicit button, so no auto-start here (unlike
            -- `startDrillIfIdle` for the whole-pool modes).
            ( { model | selectedLesson = Just id, drill = Nothing, typed = noTypedStrokes }
            , Cmd.none
            )

        PrevLesson ->
            stepLesson -1 model

        NextLesson ->
            stepLesson 1 model

        BackToLessonList ->
            ( { model | selectedLesson = Nothing, drill = Nothing, typed = noTypedStrokes }
            , Cmd.none
            )

        StartLessonDrill words ->
            -- The same shuffle path the Words mode uses: the shuffled list
            -- comes back as `ShuffledWords`, which starts the drill.
            ( model
            , Random.generate ShuffledWords (shuffleGenerator words)
            )

        QueryChanged query ->
            ( { model | query = query }, Cmd.none )

        ToggleHints ->
            ( { model | hints = not model.hints }, Cmd.none )

        ShuffledWords words ->
            -- The first shuffle of a mode (after its list loads, or on
            -- switching to it) has no drill yet, so it starts one; every later
            -- one is a pass boundary reshuffling the existing drill in place
            -- (see `IncomingBytes` below).
            let
                newDrill =
                    case model.drill of
                        Just drill ->
                            Drill.reshuffle words drill

                        Nothing ->
                            Drill.init words
            in
            ( { model | drill = Just newDrill }, Cmd.none )

        ToggleNotation ->
            ( { model | notation = Notation.toggle model.notation }, Cmd.none )

        ClickConnect ->
            ( model, Ports.requestConnect () )

        SerialStatusChanged status ->
            ( { model | serial = parseSerialStatus status }, Cmd.none )

        IncomingBytes bytes ->
            case GeminiPr.decodePacket bytes of
                Ok labels ->
                    let
                        observed =
                            labels
                                |> List.filterMap (\label -> Dict.get label model.keymap)
                                |> Set.fromList
                    in
                    case model.drill of
                        Just drill ->
                            let
                                ( newDrill, passCompleted ) =
                                    Drill.applyStroke observed drill

                                shuffleCmd =
                                    if passCompleted then
                                        case activeItems model of
                                            Just (Loaded words) ->
                                                Random.generate ShuffledWords (shuffleGenerator words)

                                            _ ->
                                                Cmd.none

                                    else
                                        Cmd.none
                            in
                            ( { model
                                | drill = Just newDrill
                                , lastStroke = observed
                                , typed =
                                    if newDrill.feedback == Just True then
                                        recordTypedStroke observed drill model.typed

                                    else
                                        model.typed
                              }
                            , shuffleCmd
                            )

                        Nothing ->
                            ( { model | lastStroke = observed }, Cmd.none )

                Err _ ->
                    -- Malformed packet -- ignore.
                    ( model, Cmd.none )


mergeAffix : Maybe Lessons.AffixData -> Lessons -> Lessons
mergeAffix affixData lessons =
    case affixData of
        Just data ->
            Lessons.mergeAffixData data lessons

        Nothing ->
            lessons


noTypedStrokes : TypedStrokes
noTypedStrokes =
    { strokes = [], complete = False }


{-| Add the stroke `drill` was expecting (just matched) to the typed-strokes
line: a new line after a completed word, otherwise appended. A stroke
completes the word when it's the last of the item, or of the current
sentence word. -}
recordTypedStroke : Set.Set Int -> Drill.State -> TypedStrokes -> TypedStrokes
recordTypedStroke observed drill typed =
    case Drill.currentWord drill of
        Just word ->
            let
                index =
                    drill.currentStrokeIndex

                -- the outline being typed: an alternate (long) one when the learner chose it
                outline =
                    Drill.matchedOutline observed drill
                        |> Maybe.withDefault { steno = word.steno, strokes = word.strokes }

                stroke =
                    String.words outline.steno
                        |> List.concatMap (String.split "/")
                        |> List.drop index
                        |> List.head
                        |> Maybe.withDefault ""

                wordEnds =
                    if List.isEmpty word.segments then
                        [ List.length outline.strokes ]

                    else
                        word.segments
                            |> List.foldl (\segment ends -> (segment.strokeCount + (List.head ends |> Maybe.withDefault 0)) :: ends) []

                complete =
                    List.member (index + 1) wordEnds
            in
            if typed.complete then
                { strokes = [ stroke ], complete = complete }

            else
                { strokes = typed.strokes ++ [ stroke ], complete = complete }

        Nothing ->
            typed


{-| The current drill mode's list; `Nothing` in definition mode (no drill)
and in lesson mode until a lesson is picked (the drill runs over the selected
lesson's own pool, not a whole exported file). The returned list is also the
pass-boundary reshuffle source, so finishing a lesson's pass deals a fresh
shuffle of that same lesson. -}
activeItems : Model -> Maybe (LoadState (List PracticeWord))
activeItems model =
    case model.mode of
        WordMode ->
            Just model.words

        SentenceMode ->
            Just model.sentences

        DefinitionMode ->
            Nothing

        LessonMode ->
            case model.lessons of
                Just (Loaded lessons) ->
                    model.selectedLesson
                        |> Maybe.andThen (\id -> lessons.lessons |> List.filter (\l -> l.id == id) |> List.head)
                        |> Maybe.map (\lesson -> Loaded lesson.words)

                _ ->
                    Nothing


{-| One step through the GLOBAL lesson order (the flat `lessons` list, i.e. the
tracks' concatenation): lands on the target lesson's INTRO by reusing the
`SelectLesson` path verbatim, so the drill state and the typed-strokes line
reset exactly as a fresh pick does. Out-of-range steps and a missing selection
are no-ops (the buttons are already disabled there). -}
stepLesson : Int -> Model -> ( Model, Cmd Msg )
stepLesson delta model =
    case model.lessons of
        Just (Loaded lessons) ->
            let
                target =
                    model.selectedLesson
                        |> Maybe.andThen (\id -> lessonIndexIn id lessons.lessons)
                        |> Maybe.andThen (\i -> List.drop (i + delta) lessons.lessons |> List.head)
            in
            case target of
                Just lesson ->
                    update (SelectLesson lesson.id) model

                Nothing ->
                    ( model, Cmd.none )

        _ ->
            ( model, Cmd.none )


lessonIndexIn : String -> List Lessons.Lesson -> Maybe Int
lessonIndexIn id lessons =
    let
        step index remaining =
            case remaining of
                [] ->
                    Nothing

                first :: rest ->
                    if first.id == id then
                        Just index

                    else
                        step (index + 1) rest
    in
    step 0 lessons


{-| Shuffle the current mode's list into a fresh drill, once it has loaded
and unless a drill is already running. -}
startDrillIfIdle : Model -> ( Model, Cmd Msg )
startDrillIfIdle model =
    case ( model.drill, activeItems model ) of
        ( Nothing, Just (Loaded items) ) ->
            ( model, Random.generate ShuffledWords (shuffleGenerator items) )

        _ ->
            ( model, Cmd.none )


{-| A plain shuffle-by-random-key: pair each word with an independent random
float and sort by that key. Good enough for a practice-order shuffle without
pulling in a dedicated shuffle package for one function. -}
shuffleGenerator : List a -> Random.Generator (List a)
shuffleGenerator list =
    Random.list (List.length list) (Random.float 0 1)
        |> Random.map
            (\keys ->
                List.map2 Tuple.pair keys list
                    |> List.sortBy Tuple.first
                    |> List.map Tuple.second
            )


parseSerialStatus : String -> SerialStatus
parseSerialStatus status =
    case status of
        "unsupported" ->
            Unsupported

        "connected" ->
            Connected

        "disconnected" ->
            Disconnected

        _ ->
            Disconnected


httpErrorToString : Http.Error -> String
httpErrorToString err =
    case err of
        Http.BadUrl url ->
            "Bad URL: " ++ url

        Http.Timeout ->
            "Request timed out"

        Http.NetworkError ->
            "Network error"

        Http.BadStatus code ->
            "Server returned status " ++ String.fromInt code

        Http.BadBody message ->
            "Could not decode response: " ++ message


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.batch
        [ Ports.serialStatus SerialStatusChanged
        , Ports.incomingBytes IncomingBytes
        ]


{-| Two columns: a narrow left sidebar carrying the title, the connect
button, the notation toggle and the two plain-text legends (too easy to lose
below the tall keyboards otherwise), and the actual trainer -- drill,
interactive keyboard, second chord-layer keyboard -- to its right, starting
at the top of the page.
-}
view : Model -> Html Msg
view model =
    div [ class "app" ]
        [ div [ class "sidebar" ]
            (h1 [] [ text "Stenalgo practice" ]
                :: viewConnectButton model.serial
                :: viewModeSwitch model.mode
                :: viewHintsToggle model
                :: viewNotationToggle model.notation
                :: viewSidebarLegends model
            )
        , div [ class "main" ]
            [ case model.serial of
                Unsupported ->
                    p [ class "unsupported" ]
                        [ text "This browser doesn't support the Web Serial API. Use Chrome or Edge to practice with real hardware." ]

                _ ->
                    viewTrainer model
            ]
        ]


{-| Nothing on a browser without Web Serial -- the main column says why instead. -}
viewConnectButton : SerialStatus -> Html Msg
viewConnectButton serial =
    case serial of
        Unsupported ->
            text ""

        _ ->
            button
                [ class "connect-button", onClick ClickConnect, disabled (serial == Connected) ]
                [ text
                    (if serial == Connected then
                        "Connected"

                     else
                        "Connect steno machine"
                    )
                ]


viewModeSwitch : Mode -> Html Msg
viewModeSwitch mode =
    let
        modeButton target name =
            button [ onClick (SwitchMode target), disabled (mode == target) ] [ text name ]
    in
    p [ class "mode-switch" ]
        [ modeButton WordMode "Words"
        , text " "
        , modeButton SentenceMode "Sentences"
        , text " "
        , modeButton DefinitionMode "Definitions"
        , text " "
        , modeButton LessonMode "Lessons"
        ]


{-| Hints on: the keyboard lights up the keys of the expected stroke and the
drill shows its chord. Off: the keyboard shows only the keys you typed, and
the chord line becomes the strokes typed so far (see `TypedStrokes`). -}
viewHintsToggle : Model -> Html Msg
viewHintsToggle model =
    if model.mode == DefinitionMode then
        text ""

    else
        p [ class "hints-toggle" ]
            [ text
                (if model.hints then
                    "Hints: on "

                 else
                    "Hints: off "
                )
            , button [ onClick ToggleHints ]
                [ text
                    (if model.hints then
                        "Hide hints"

                     else
                        "Show hints"
                    )
                ]
            ]


{-| Switches every phoneme on the page -- keys, chord board, legends, the
drill's steno and phonology -- between X-SAMPA (what the dictionary is
written in) and IPA. See `Notation`. -}
viewNotationToggle : Notation -> Html Msg
viewNotationToggle notation =
    p [ class "notation-toggle" ]
        [ text ("Phonemes: " ++ Notation.label notation ++ " ")
        , button [ onClick ToggleNotation ] [ text ("Show " ++ Notation.label (Notation.toggle notation)) ]
        ]


viewSidebarLegends : Model -> List (Html Msg)
viewSidebarLegends model =
    case model.layout of
        Loaded layout ->
            [ Keyboard.viewLegends (Notation.layout model.notation layout)
                (model.affixData
                    |> Maybe.map .rules
                    |> Maybe.withDefault []
                    |> List.map (\rule -> { rule | keyNames = List.map (Notation.render model.notation) rule.keyNames })
                )
            ]

        _ ->
            []


viewTrainer : Model -> Html Msg
viewTrainer model =
    div []
        [ case ( model.mode, activeItems model ) of
            ( DefinitionMode, _ ) ->
                viewDefinitions model

            ( LessonMode, _ ) ->
                viewLessons model

            ( _, Just (Failed message) ) ->
                p [ class "error" ] [ text ("Couldn't load practice " ++ modeNoun model.mode ++ ": " ++ message) ]

            ( _, Just (Loaded _) ) ->
                viewDrill model

            _ ->
                p [] [ text ("Loading practice " ++ modeNoun model.mode ++ "...") ]
        , if model.mode == LessonMode && model.drill == Nothing then
            -- The lesson intro renders its own keyboard (highlighting the
            -- lesson's new keys/chords); the list has nothing to highlight.
            text ""

          else
            case model.layout of
                Failed message ->
                    p [ class "error" ] [ text ("Couldn't load keyboard layout: " ++ message) ]

                Loading ->
                    p [] [ text "Loading keyboard layout..." ]

                Loaded loadedLayout ->
                    let
                        layout =
                            Notation.layout model.notation loadedLayout
                    in
                    div []
                        [ Keyboard.view
                            (if model.hints && model.mode /= DefinitionMode then
                                { highlighted = model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty
                                , correct = model.drill |> Maybe.andThen .feedback
                                }

                             else
                                { highlighted = model.lastStroke
                                , correct = model.drill |> Maybe.andThen .feedback
                                }
                            )
                            layout.keys
                        , Keyboard.viewChordBoard layout
                        ]
        ]


modeNoun : Mode -> String
modeNoun mode =
    case mode of
        WordMode ->
            "words"

        SentenceMode ->
            "sentences"

        DefinitionMode ->
            "definitions"

        LessonMode ->
            "lessons"


viewDefinitions : Model -> Html Msg
viewDefinitions model =
    div [ class "definitions" ]
        [ input
            [ type_ "search"
            , class "definition-query"
            , placeholder "Spelling, e.g. est"
            , value model.query
            , onInput QueryChanged
            , autofocus True
            ]
            []
        , case model.definitions of
            Just (Loaded definitions) ->
                Definitions.view (Notation.render model.notation) model.query definitions

            Just (Failed message) ->
                p [ class "error" ] [ text ("Couldn't load definitions: " ++ message) ]

            _ ->
                p [] [ text "Loading definitions..." ]
        ]


{-| Lesson mode's three screens: the picker (no lesson selected), the intro
of the selected lesson, and -- once its "Start drill" has gone through the
shuffle -- the shared drill view over that lesson's words, with a back link
above it so a run can be abandoned without leaving the mode. Both the intro
and the drill page carry the Previous/Next pair over the global lesson order
(`Lessons.viewPrevNext`); both land on the target lesson's intro. The
keyboard under the drill is the trainer's usual one (hints follow the drill);
the intro carries its own (see `Lessons.viewIntro`). -}
viewLessons : Model -> Html Msg
viewLessons model =
    case model.lessons of
        Just (Failed message) ->
            p [ class "error" ] [ text ("Couldn't load lessons: " ++ message) ]

        Just (Loaded lessons) ->
            let
                selected =
                    model.selectedLesson
                        |> Maybe.andThen (\id -> lessons.lessons |> List.filter (\l -> l.id == id) |> List.head)

                ( onPrev, onNext ) =
                    let
                        length =
                            List.length lessons.lessons
                    in
                    case model.selectedLesson |> Maybe.andThen (\id -> lessonIndexIn id lessons.lessons) of
                        Just index ->
                            ( (if index > 0 then Just PrevLesson else Nothing)
                            , (if index < length - 1 then Just NextLesson else Nothing)
                            )

                        Nothing ->
                            ( Nothing, Nothing )
            in
            case selected of
                Just lesson ->
                    if model.drill == Nothing then
                        Lessons.viewIntro
                            { onBack = BackToLessonList
                            , onStart = StartLessonDrill
                            , onPrev = onPrev
                            , onNext = onNext
                            , render = Notation.render model.notation
                            , keys =
                                case model.layout of
                                    Loaded layout ->
                                        (Notation.layout model.notation layout).keys

                                    _ ->
                                        []
                            }
                            lesson

                    else
                        div [ class "lesson-drill" ]
                            [ p [ class "lesson-back" ]
                                ([ button [ onClick BackToLessonList ] [ text "← Lessons" ] ]
                                    ++ Lessons.viewPrevNext onPrev onNext
                                )
                            , viewDrill model
                            ]

                Nothing ->
                    Lessons.viewList
                        { onSelect = SelectLesson
                        , selected = model.selectedLesson
                        , render = Notation.render model.notation
                        }
                        lessons

        _ ->
            p [] [ text "Loading lessons..." ]


viewDrill : Model -> Html Msg
viewDrill model =
    case ( model.drill, model.drill |> Maybe.andThen Drill.currentWord ) of
        ( Just drill, Just word ) ->
            let
                reservedKeys =
                    case model.layout of
                        Loaded layout ->
                            layout.keys |> List.filter .reserved |> List.map .index |> Set.fromList

                        _ ->
                            Set.empty

                chordDisplay =
                    if model.hints then
                        ShowChord model.notation reservedKeys

                    else
                        ShowTyped model.notation model.typed
            in
            case model.mode of
                SentenceMode ->
                    viewSentence chordDisplay (Drill.currentSegmentIndex drill) word

                _ ->
                    div [ class "drill" ]
                        [ div [ class "drill-words" ]
                            [ div [ class "current-word" ]
                                (p [ class "target-word" ] (viewInContext word)
                                    :: viewReading chordDisplay word.label word.phonology word.steno word.strokes
                                )
                            , p [ class "next-word" ]
                                (Drill.nextWord drill |> Maybe.map viewInContext |> Maybe.withDefault [ text "\u{00A0}" ])
                            ]
                        ]

        _ ->
            p [] [ text "Nothing to practice." ]


{-| A drilled word between its de-emphasized context words ("la maison",
"que tu viennes", "parle !"), joined without a space after an elision ("l'",
"j'", "qu'il"). -}
viewInContext : PracticeWord -> List (Html Msg)
viewInContext word =
    let
        context string =
            Html.span [ class "context-word" ] [ text string ]

        beforePart =
            if String.isEmpty word.before then
                []

            else if String.endsWith "'" word.before then
                [ context word.before ]

            else
                [ context (word.before ++ " ") ]

        afterPart =
            if String.isEmpty word.after then
                []

            else
                [ context (" " ++ word.after) ]
    in
    beforePart ++ [ text word.ortho ] ++ afterPart


{-| A sentence with its current word highlighted (words already written
dimmed), and that word's reading/phonology/chord underneath -- the whole
sentence's chords at once would be unreadable. `phonology` holds one
space-separated transcription per word, parallel to `segments`. -}
viewSentence : ChordDisplay -> Int -> PracticeWord -> Html Msg
viewSentence chordDisplay currentIndex sentence =
    let
        segmentStart index =
            sentence.segments |> List.take index |> List.map .strokeCount |> List.sum

        wordClass index =
            if index < currentIndex then
                "sentence-word done"

            else if index == currentIndex then
                "sentence-word current"

            else
                "sentence-word"

        -- Elided words ("j'") and inversions ("-tu") attach to their neighbour.
        spaceBefore index segment =
            if index == 0 || String.startsWith "-" segment.text then
                ""

            else
                case List.drop (index - 1) sentence.segments |> List.head of
                    Just previous ->
                        if String.endsWith "'" previous.text then
                            ""

                        else
                            " "

                    Nothing ->
                        " "

        displayText index segment =
            if index == 0 then
                String.toUpper (String.left 1 segment.text) ++ String.dropLeft 1 segment.text

            else
                segment.text

        finalPunctuation =
            String.right 1 sentence.ortho
                |> (\c ->
                        if String.contains c ".?!" then
                            " " ++ c

                        else
                            ""
                   )
    in
    div [ class "drill" ]
        [ div [ class "current-word" ]
            (p [ class "target-sentence" ]
                (List.indexedMap
                    (\index segment ->
                        Html.span []
                            [ text (spaceBefore index segment)
                            , Html.span [ class (wordClass index) ] [ text (displayText index segment) ]
                            ]
                    )
                    sentence.segments
                    ++ [ text finalPunctuation ]
                )
                :: (case List.drop currentIndex sentence.segments |> List.head of
                        Just segment ->
                            viewReading chordDisplay
                                segment.label
                                (String.split " " sentence.phonology |> List.drop currentIndex |> List.head |> Maybe.withDefault "")
                                segment.steno
                                (sentence.strokes |> List.drop (segmentStart currentIndex) |> List.take segment.strokeCount)

                        Nothing ->
                            []
                   )
            )
        ]


{-| How a drilled word's chord line is shown: the chord itself (hints on,
with the reserved keys to split its bare mark strokes off), or the strokes
typed so far (hints off). -}
type ChordDisplay
    = ShowChord Notation (Set.Set Int)
    | ShowTyped Notation TypedStrokes


{-| One word's reading label, phonology and chord (or, hints off, the
strokes typed so far -- see `ChordDisplay`). Reserved keys (`*`, `#`,
and the two still-unassigned ones) never carry a phoneme: they're the `*`/`#`
track's mark, which picks which *lemma* you mean among homophones of
different words (`src/ambiguitychecker.py`'s "lemma-homophone ambiguity",
e.g. a/à/as), not a conjugated form of one lemma (that's Phase P's separate
mechanism, an extra stroke of ordinary coda keys -- see the sidebar's
"Conjugation markers" legend). The mark's first symbol is pressed with the
word's last phoneme stroke ("a*"), so it stays in the chord; only a large
homophone cluster's further symbols are strokes of their own, split onto
their own line under the chord -- always rendered (even empty) so a word that
has one doesn't shift the layout of the one after it.
-}
viewReading : ChordDisplay -> String -> String -> String -> List (List Int) -> List (Html Msg)
viewReading chordDisplay label phonology steno strokes =
    let
        orSpace string =
            if String.isEmpty string then
                "\u{00A0}"

            else
                string
    in
    case chordDisplay of
        ShowChord notation reservedKeys ->
            let
                isMarkStroke stroke =
                    not (List.isEmpty stroke) && List.all (\k -> Set.member k reservedKeys) stroke

                strokeParts =
                    List.map2 Tuple.pair (String.split "/" steno) strokes

                basePart =
                    strokeParts |> List.filter (\( _, stroke ) -> not (isMarkStroke stroke)) |> List.map Tuple.first |> String.join "/"

                markPart =
                    strokeParts |> List.filter (\( _, stroke ) -> isMarkStroke stroke) |> List.map Tuple.first |> String.join "/"
            in
            [ p [ class "target-label" ] [ text label ]
            , p [ class "target-phonology" ] [ text ("/" ++ Notation.render notation phonology ++ "/") ]
            , p [ class "target-steno" ] [ text (Notation.render notation basePart) ]
            , p [ class "target-mark" ] [ text (orSpace markPart) ]
            ]

        ShowTyped notation typed ->
            [ p [ class "target-label" ] [ text label ]
            , p [ class "target-phonology" ] [ text ("/" ++ Notation.render notation phonology ++ "/") ]
            , p [ class "target-steno typed-strokes" ]
                [ text
                    (orSpace
                        (Notation.render notation (String.join "/" typed.strokes)
                            ++ (if typed.complete then
                                    " \u{2713}"

                                else
                                    ""
                               )
                        )
                    )
                ]
            , p [ class "target-mark" ] [ text "\u{00A0}" ]
            ]
