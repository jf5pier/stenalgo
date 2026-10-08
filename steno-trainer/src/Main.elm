module Main exposing (main)

import Browser
import Definitions exposing (Definitions)
import Dict exposing (Dict)
import Drill exposing (PracticeWord)
import GeminiPr
import Html exposing (Html, button, div, h1, h2, input, p, span, text)
import Html.Attributes exposing (autofocus, class, classList, disabled, placeholder, type_, value)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode as D
import Keyboard exposing (KeyInfo, Layout)
import Lessons exposing (Lessons)
import Notation exposing (Notation)
import Style exposing (NumberStyle, Style)
import PloverHid
import Ports
import Process
import Random
import Set
import Task


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
    = IntroMode
    | WordMode
    | SentenceMode
    | DefinitionMode
    | LessonMode


{-| The modes without a drill (no hints, no keyboard of their own). -}
isInfoMode : Mode -> Bool
isInfoMode mode =
    mode == DefinitionMode || mode == IntroMode


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
    | ConnectError String


type alias Model =
    { layout : LoadState Layout
    , words : LoadState (List PracticeWord)
    , sentences : LoadState (List PracticeWord)
    , mode : Mode
    , drill : Maybe Drill.State
    , keymap : Dict String Int
    , serial : SerialStatus
    , notation : Notation
    , style : Style -- the punctuation and command chord set taught and shown: Plover (default) or Pluvier
    , numberStyle : NumberStyle -- the number theory taught and shown: Pluvier's bar (default) or Lapwing's numpad
    , definitions : Maybe (LoadState Definitions)
    , expressionDefinitions : Definitions.ExpressionDefinitions -- expression-definitions.json (attach words, composed phrases), optional
    , abbreviations : Dict String (Dict String String) -- affix-abbreviations.json (spelling -> long outline -> short), optional
    , wordRules : Dict String (List Int) -- affix-word-rules.json (lowercase spelling -> ranks of the affix rules shortening it), optional
    , lessons : Maybe (LoadState Lessons)
    , affixData : Maybe Lessons.AffixData -- affix-lessons.json, when it came back (the stub stays otherwise)
    , expressionData : Maybe Lessons.ExpressionData -- expression-lessons.json: the rules legend and the expressions lessons, when it came back
    , punctuationData : Maybe Lessons.PunctuationData -- punctuation-lessons.json: the punctuation and command tracks of both styles, when it came back
    , spellingData : Maybe Lessons.SpellingData -- spelling-lessons.json: the epellation track, when it came back
    , numberData : Maybe Lessons.NumberData -- number-lessons.json: the chiffres track of both number theories, when it came back
    , expressionSentences : Maybe (List PracticeWord) -- expression-sentences.json (abbreviated sentences), optional
    , abbreviatedSentences : Bool -- Sentences mode drills `expressionSentences` instead of the plain sentences
    , selectedLesson : Maybe String
    , query : String
    , hints : Bool
    , lessonMix : Bool -- the lesson drill mixes the current lesson's words 50/50 with those of the past lessons (default: current only)
    , simulation : Maybe Simulation -- the Simulate button's run in progress
    , simulationRuns : Int -- runs started so far; a timer of an older run is ignored
    , abbrevHints : Maybe Bool -- the learner's choice for the abbreviation rule hint; Nothing = the default (`abbrevHintsOn`)
    , lastStroke : Set.Set Int
    , wrongRuns : Int -- wrong strokes so far; the 2 s red flash of an older one is ignored
    , typed : TypedStrokes
    }


{-| The Simulate button's run: the strokes to light one after the other and the
one currently lit. `run` tells the timers of this run from an older one's. -}
type alias Simulation =
    { run : Int
    , strokes : List (List Int)
    , step : Int
    , phonology : String -- Definitions page only: the clicked word's (raw X-SAMPA) phonology, for the 2-/3-/4-key phoneme boards
    }


type Msg
    = GotLayout (Result Http.Error Layout)
    | GotWords (Result Http.Error (List PracticeWord))
    | GotSentences (Result Http.Error (List PracticeWord))
    | SwitchMode Mode
    | ShuffledWords (List PracticeWord)
    | ClickConnect
    | ClickConnectHid
    | IncomingHidChord (List Int)
    | SerialStatusChanged String
    | IncomingBytes (List Int)
    | ClearWrong Int
    | ToggleNotation
    | ToggleStyle
    | ToggleNumberStyle
    | GotDefinitions (Result Http.Error Definitions)
    | GotExpressionDefinitions (Result Http.Error Definitions.ExpressionDefinitions)
    | GotAbbreviations (Result Http.Error (Dict String (Dict String String)))
    | GotWordRules (Result Http.Error (Dict String (List Int)))
    | GotLessons (Result Http.Error Lessons)
    | GotAffixData (Result Http.Error Lessons.AffixData)
    | GotExpressionData (Result Http.Error Lessons.ExpressionData)
    | GotPunctuationData (Result Http.Error Lessons.PunctuationData)
    | GotNumberData (Result Http.Error Lessons.NumberData)
    | GotSpellingData (Result Http.Error Lessons.SpellingData)
    | GotExpressionSentences (Result Http.Error (List PracticeWord))
    | ToggleAbbreviatedSentences
    | SelectLesson String
    | PrevLesson
    | NextLesson
    | BackToLessonList
    | StartLessonDrill (List PracticeWord)
    | ToggleLessonMix
    | QueryChanged String
    | ToggleHints
    | ToggleAbbrevHints
    | SkipWords Int
    | StartSimulation
    | SimulateOutline String String
    | SimulationStep Int Int


{-| `Http.get` that always revalidates (the exported JSON changes with every
rebuild, and a static server's Last-Modified lets browsers keep a stale copy). -}
getFresh : { url : String, expect : Http.Expect msg } -> Cmd msg
getFresh { url, expect } =
    Http.request
        { method = "GET"
        , headers = [ Http.header "Cache-Control" "no-cache" ]
        , url = url
        , body = Http.emptyBody
        , expect = expect
        , timeout = Nothing
        , tracker = Nothing
        }


main : Program () Model Msg
main =
    Browser.element { init = init, update = update, subscriptions = subscriptions, view = view }


init : () -> ( Model, Cmd Msg )
init _ =
    ( { layout = Loading
      , words = Loading
      , sentences = Loading
      , mode = IntroMode
      , drill = Nothing
      , keymap = Dict.empty
      , serial = CheckingSupport
      , notation = Notation.XSampa
      , style = Style.Plover
      , numberStyle = Style.PluvierNumbers
      , definitions = Nothing
      , expressionDefinitions = Definitions.emptyExpressions
      , abbreviations = Dict.empty
      , wordRules = Dict.empty
      , lessons = Nothing
      , affixData = Nothing
      , expressionData = Nothing
      , punctuationData = Nothing
      , spellingData = Nothing
      , numberData = Nothing
      , expressionSentences = Nothing
      , abbreviatedSentences = False
      , selectedLesson = Nothing
      , query = ""
      , hints = True
      , lessonMix = False
      , abbrevHints = Nothing
      , simulation = Nothing
      , simulationRuns = 0
      , lastStroke = Set.empty
      , wrongRuns = 0
      , typed = noTypedStrokes
      }
    , Cmd.batch
        [ getFresh { url = "public/data/keyboard-layout.json", expect = Http.expectJson GotLayout Keyboard.decoder }
        , getFresh { url = "public/data/practice-words.json", expect = Http.expectJson GotWords Drill.decoder }
        , getFresh { url = "public/data/practice-sentences.json", expect = Http.expectJson GotSentences Drill.sentenceDecoder }
        , getFresh { url = "public/data/affix-lessons.json", expect = Http.expectJson GotAffixData Lessons.affixDecoder }
        , getFresh { url = "public/data/affix-word-rules.json", expect = Http.expectJson GotWordRules (D.dict (D.list D.int)) }
        , getFresh { url = "public/data/expression-lessons.json", expect = Http.expectJson GotExpressionData Lessons.expressionDecoder }
        , getFresh { url = "public/data/punctuation-lessons.json", expect = Http.expectJson GotPunctuationData Lessons.punctuationDecoder }
        , getFresh { url = "public/data/spelling-lessons.json", expect = Http.expectJson GotSpellingData Lessons.spellingDecoder }
        , getFresh { url = "public/data/number-lessons.json", expect = Http.expectJson GotNumberData Lessons.numberDecoder }
        , getFresh { url = "public/data/expression-sentences.json", expect = Http.expectJson GotExpressionSentences Drill.sentenceDecoder }
        ]
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg unswitched =
    let
        -- Changing mode ends a Simulate run (its timers are then ignored).
        model =
            case msg of
                SwitchMode _ ->
                    { unswitched | simulation = Nothing }

                _ ->
                    unswitched
    in
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
                , Cmd.batch
                    [ getFresh { url = "public/data/definitions.json", expect = Http.expectJson GotDefinitions Definitions.decoder }
                    , getFresh { url = "public/data/affix-abbreviations.json", expect = Http.expectJson GotAbbreviations (D.dict (D.dict D.string)) }
                    , getFresh { url = "public/data/expression-definitions.json", expect = Http.expectJson GotExpressionDefinitions Definitions.expressionsDecoder }
                    ]
                )

            else if mode == LessonMode && model.lessons == Nothing then
                ( { model | mode = mode, drill = Nothing, typed = noTypedStrokes, selectedLesson = Nothing, lessons = Just Loading }
                , getFresh { url = "public/data/lessons.json", expect = Http.expectJson GotLessons Lessons.decoder }
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

        GotAbbreviations (Ok abbreviations) ->
            ( { model | abbreviations = abbreviations }, Cmd.none )

        GotExpressionDefinitions (Ok expressions) ->
            ( { model | expressionDefinitions = expressions }, Cmd.none )

        GotExpressionDefinitions (Err _) ->
            -- Optional layer: without the file the Definitions page has no attach or composed entries.
            ( model, Cmd.none )

        GotAbbreviations (Err _) ->
            -- Optional layer: without the file the Definitions page has no abbreviation column.
            ( model, Cmd.none )

        GotWordRules (Ok wordRules) ->
            ( { model | wordRules = wordRules }, Cmd.none )

        GotWordRules (Err _) ->
            -- Optional layer: without the file only the affix lessons' words have a rule hint.
            ( model, Cmd.none )

        GotDefinitions (Ok definitions) ->
            ( { model | definitions = Just (Loaded definitions) }, Cmd.none )

        GotDefinitions (Err err) ->
            ( { model | definitions = Just (Failed (httpErrorToString err)) }, Cmd.none )

        GotLessons (Ok lessons) ->
            ( { model | lessons = Just (Loaded (mergeOptionalData model lessons)) }, Cmd.none )

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

        GotExpressionData (Ok data) ->
            -- Same as the affix file: whichever of lessons.json / expression-lessons.json arrives last merges.
            ( { model
                | expressionData = Just data
                , lessons =
                    case model.lessons of
                        Just (Loaded lessons) ->
                            Just (Loaded (Lessons.mergeExpressionData data lessons))

                        other ->
                            other
              }
            , Cmd.none
            )

        GotExpressionData (Err _) ->
            -- Optional layer: without the file the expressions track keeps its stub lesson.
            ( model, Cmd.none )

        GotPunctuationData (Ok data) ->
            -- Same as the other files: whichever of lessons.json / punctuation-lessons.json arrives last merges.
            ( { model
                | punctuationData = Just data
                , lessons =
                    case model.lessons of
                        Just (Loaded lessons) ->
                            Just (Loaded (Lessons.mergePunctuationData model.style data lessons))

                        other ->
                            other
              }
            , Cmd.none
            )

        GotPunctuationData (Err _) ->
            -- Optional layer: without the file there are no punctuation and command tracks.
            ( model, Cmd.none )

        GotNumberData (Ok data) ->
            ( { model
                | numberData = Just data
                , lessons =
                    case model.lessons of
                        Just (Loaded lessons) ->
                            Just (Loaded (Lessons.mergeNumberData model.numberStyle model.style data lessons))

                        other ->
                            other
              }
            , Cmd.none
            )

        GotNumberData (Err _) ->
            -- Optional layer: without the file there is no chiffres track.
            ( model, Cmd.none )

        GotSpellingData (Ok data) ->
            ( { model
                | spellingData = Just data
                , lessons =
                    case model.lessons of
                        Just (Loaded lessons) ->
                            Just (Loaded (Lessons.mergeSpellingData data lessons))

                        other ->
                            other
              }
            , Cmd.none
            )

        GotSpellingData (Err _) ->
            -- Optional layer: without the file there is no epellation track.
            ( model, Cmd.none )

        GotExpressionSentences (Ok sentences) ->
            ( { model | expressionSentences = Just sentences }, Cmd.none )

        GotExpressionSentences (Err _) ->
            -- Optional layer: without the file Sentences mode has no abbreviated-sentences switch.
            ( model, Cmd.none )

        ToggleAbbreviatedSentences ->
            -- A fresh drill over the other sentence list (the same restart a mode switch does).
            startDrillIfIdle
                { model
                    | abbreviatedSentences = not model.abbreviatedSentences
                    , drill = Nothing
                    , typed = noTypedStrokes
                }

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

        StartLessonDrill fallbackWords ->
            -- The same shuffle path the Words mode uses: the shuffled list
            -- comes back as `ShuffledWords`, which starts the drill. The words
            -- are the lesson's drill mix (`activeItems`), not the whole pool.
            ( model
            , Random.generate ShuffledWords
                (shuffleGenerator
                    (case activeItems model of
                        Just (Loaded words) ->
                            words

                        _ ->
                            fallbackWords
                    )
                )
            )

        ToggleLessonMix ->
            let
                switched =
                    { model | lessonMix = not model.lessonMix }
            in
            ( switched
            , case activeItems switched of
                Just (Loaded words) ->
                    Random.generate ShuffledWords (shuffleGenerator words)

                _ ->
                    Cmd.none
            )

        QueryChanged query ->
            ( { model | query = query }, Cmd.none )

        ToggleHints ->
            ( { model | hints = not model.hints }, Cmd.none )

        ToggleAbbrevHints ->
            ( { model | abbrevHints = Just (not (abbrevHintsOn model)) }, Cmd.none )

        StartSimulation ->
            case currentStrokes model of
                [] ->
                    ( model, Cmd.none )

                strokes ->
                    let
                        run =
                            model.simulationRuns + 1
                    in
                    ( { model | simulation = Just { run = run, strokes = strokes, step = 0, phonology = "" }, simulationRuns = run }
                    , simulationTimer run 0 strokes
                    )

        SimulateOutline phonology outline ->
            case ( model.layout, model.layout |> loadedKeys |> (\keys -> Keyboard.parseOutline keys outline) ) of
                ( Loaded _, Just strokes ) ->
                    let
                        run =
                            model.simulationRuns + 1
                    in
                    ( { model | simulation = Just { run = run, strokes = strokes, step = 0, phonology = phonology }, simulationRuns = run }
                    , simulationTimer run 0 strokes
                    )

                _ ->
                    ( model, Cmd.none )

        SimulationStep run step ->
            case model.simulation of
                Just simulation ->
                    if simulation.run /= run then
                        ( model, Cmd.none )

                    else if step >= List.length simulation.strokes then
                        ( { model | simulation = Nothing }, Cmd.none )

                    else
                        ( { model | simulation = Just { simulation | step = step } }
                        , simulationTimer run step simulation.strokes
                        )

                Nothing ->
                    ( model, Cmd.none )

        SkipWords n ->
            ( { model
                | simulation = Nothing
                , drill = Maybe.map (Drill.skipWords n) model.drill
                , typed = noTypedStrokes
                , lastStroke = Set.empty
              }
            , Cmd.none
            )

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

        ToggleStyle ->
            -- The lessons of the two styles have the same ids: the selection stays, but a running lesson drill
            -- (whose items are the old style's chords) goes back to the lesson text.
            let
                style =
                    Style.toggle model.style
            in
            ( { model
                | style = style
                , lessons =
                    case ( model.lessons, model.punctuationData ) of
                        ( Just (Loaded lessons), Just data ) ->
                            Just (Loaded (mergeNumbers model.numberStyle style model.numberData (Lessons.mergePunctuationData style data lessons)))

                        ( other, _ ) ->
                            other
                , drill =
                    if model.mode == LessonMode then
                        Nothing

                    else
                        model.drill
                , typed = noTypedStrokes
                , simulation = Nothing
              }
            , Cmd.none
            )

        ToggleNumberStyle ->
            -- Same ids in both theories: the selection stays, a running lesson drill goes back to the lesson text.
            let
                numberStyle =
                    Style.toggleNumber model.numberStyle
            in
            ( { model
                | numberStyle = numberStyle
                , lessons =
                    case ( model.lessons, model.numberData ) of
                        ( Just (Loaded lessons), Just data ) ->
                            Just (Loaded (Lessons.mergeNumberData numberStyle model.style data lessons))

                        ( other, _ ) ->
                            other
                , drill =
                    if model.mode == LessonMode then
                        Nothing

                    else
                        model.drill
                , typed = noTypedStrokes
                , simulation = Nothing
              }
            , Cmd.none
            )

        ClickConnect ->
            ( model, Ports.requestConnect () )

        SerialStatusChanged status ->
            ( { model | serial = parseSerialStatus status }, Cmd.none )

        ClickConnectHid ->
            ( model, Ports.requestConnectHid () )

        IncomingHidChord bytes ->
            applyLabels (PloverHid.decodeChord bytes) model

        IncomingBytes bytes ->
            applyLabels (GeminiPr.decodePacket bytes) model

        ClearWrong token ->
            -- The red flash of a wrong stroke lasts 2 s, then the hint (gray) is back.
            case model.drill of
                Just drill ->
                    if token == model.wrongRuns && drill.feedback == Just False then
                        ( { model | drill = Just { drill | feedback = Nothing }, lastStroke = Set.empty }, Cmd.none )

                    else
                        ( model, Cmd.none )

                Nothing ->
                    ( model, Cmd.none )


{-| One decoded stroke (from either machine protocol) fed to the drill. -}
applyLabels : Result String (List String) -> Model -> ( Model, Cmd Msg )
applyLabels decoded model =
            case decoded of
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

                                wrong =
                                    newDrill.feedback == Just False

                                wrongRuns =
                                    if wrong then
                                        model.wrongRuns + 1

                                    else
                                        model.wrongRuns

                                clearCmd =
                                    if wrong then
                                        Process.sleep 2000 |> Task.perform (\_ -> ClearWrong wrongRuns)

                                    else
                                        Cmd.none

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
                                , wrongRuns = wrongRuns
                                , typed =
                                    if newDrill.feedback == Just True then
                                        recordTypedStroke observed drill model.typed

                                    else
                                        model.typed
                              }
                            , Cmd.batch [ shuffleCmd, clearCmd ]
                            )

                        Nothing ->
                            ( { model | lastStroke = observed }, Cmd.none )

                Err _ ->
                    -- Malformed packet -- ignore.
                    ( model, Cmd.none )


{-| The lessons with the `chiffres` track of the chosen theory and punctuation style, when `number-lessons.json` came back. -}
mergeNumbers : NumberStyle -> Style -> Maybe Lessons.NumberData -> Lessons.Lessons -> Lessons.Lessons
mergeNumbers numberStyle style numberData lessons =
    numberData |> Maybe.map (\data -> Lessons.mergeNumberData numberStyle style data lessons) |> Maybe.withDefault lessons


{-| `lessons.json` with the optional files that already came back merged in
(`affix-lessons.json`, `expression-lessons.json`). -}
mergeOptionalData : Model -> Lessons -> Lessons
mergeOptionalData model lessons =
    lessons
        |> (\l -> model.affixData |> Maybe.map (\data -> Lessons.mergeAffixData data l) |> Maybe.withDefault l)
        |> (\l -> model.expressionData |> Maybe.map (\data -> Lessons.mergeExpressionData data l) |> Maybe.withDefault l)
        |> (\l -> model.punctuationData |> Maybe.map (\data -> Lessons.mergePunctuationData model.style data l) |> Maybe.withDefault l)
        |> (\l -> model.numberData |> Maybe.map (\data -> Lessons.mergeNumberData model.numberStyle model.style data l) |> Maybe.withDefault l)
        |> (\l -> model.spellingData |> Maybe.map (\data -> Lessons.mergeSpellingData data l) |> Maybe.withDefault l)


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
            case ( model.abbreviatedSentences, model.expressionSentences ) of
                ( True, Just sentences ) ->
                    Just (Loaded sentences)

                _ ->
                    Just model.sentences

        IntroMode ->
            Nothing

        DefinitionMode ->
            Nothing

        LessonMode ->
            case model.lessons of
                Just (Loaded lessons) ->
                    model.selectedLesson
                        |> Maybe.andThen (\id -> lessons.lessons |> List.filter (\l -> l.id == id) |> List.head)
                        |> Maybe.map
                            (\lesson ->
                                let
                                    current =
                                        Lessons.currentWords lesson
                                in
                                if model.lessonMix then
                                    Loaded (current ++ List.take (List.length current) (Lessons.pastWords lessons lesson))

                                else
                                    Loaded current
                            )

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

        other ->
            if String.startsWith "error:" other then
                ConnectError (String.dropLeft 6 other)

            else
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
        , Ports.incomingHidChord IncomingHidChord
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
            ([ h1 [] [ text "Pratique Stenalgo fran\u{00E7}ais" ]
             , viewModeSwitch model.mode
             , viewSection "Options"
                [ viewHintsToggle model
                , viewAbbrevHintsToggle model
                , viewAbbreviatedSentencesToggle model
                , viewNotationToggle model.notation
                , viewStyleToggle model.style
                , viewNumberStyleToggle model.numberStyle
                ]
             ]
                ++ viewSidebarLegends model
                ++ [ viewSection "Connexion au clavier steno" [ viewConnectButton model.serial ] ]
            )
        , div [ class "main" ] [ viewTrainer model ]
        ]


{-| A titled block of the sidebar. -}
viewSection : String -> List (Html Msg) -> Html Msg
viewSection title content =
    div [ class "sidebar-section" ] (h2 [] [ text title ] :: content)


{-| "label : [on] [off]" -- the current choice's button is the disabled one. -}
viewOnOff : String -> Bool -> Msg -> Html Msg
viewOnOff label isOn toggle =
    p [ class "hints-toggle" ]
        [ text (label ++ " : ")
        , button [ onClick toggle, disabled isOn ] [ text "on" ]
        , text " "
        , button [ onClick toggle, disabled (not isOn) ] [ text "off" ]
        ]


{-| The Introduction page, the default landing. Its text is still to be written
(see TODO.md). -}
viewIntroPage : Html Msg
viewIntroPage =
    div [ class "intro-page" ]
        [ h1 [] [ text "Introduction" ]
        , p [] [ text "\u{00C0} venir." ]
        ]


{-| One button per protocol, Gemini PR (Web Serial) and Plover HID (WebHID); both
APIs exist only in Chrome and Edge, which the browser-less case spells out. -}
viewConnectButton : SerialStatus -> Html Msg
viewConnectButton serial =
    case serial of
        Unsupported ->
            p [ class "unsupported" ] [ text "Ce navigateur ne g\u{00E8}re ni Web Serial ni WebHID : utilisez Chrome ou Edge pour pratiquer avec le clavier." ]

        _ ->
            div [ class "connect-buttons" ]
                [ button [ class "connect-button", onClick ClickConnect, disabled (serial == Connected) ] [ text "Gemini PR" ]
                , text " "
                , button [ class "connect-button", onClick ClickConnectHid, disabled (serial == Connected) ] [ text "Plover HID (chrome/edge only)" ]
                , case serial of
                    Connected ->
                        p [] [ text "Connect\u{00E9}." ]

                    ConnectError message ->
                        p [ class "unsupported" ] [ text ("\u{00C9}chec de la connexion : " ++ message) ]

                    _ ->
                        text ""
                ]


viewModeSwitch : Mode -> Html Msg
viewModeSwitch mode =
    let
        modeButton target name =
            button [ onClick (SwitchMode target), disabled (mode == target) ] [ text name ]
    in
    div [ class "mode-switch" ]
        [ modeButton IntroMode "Introduction"
        , modeButton LessonMode "Le\u{00E7}ons"
        , modeButton WordMode "Mots"
        , modeButton SentenceMode "Phrases"
        , modeButton DefinitionMode "D\u{00E9}finitions"
        ]


{-| Hints on: the keyboard lights up the keys of the expected stroke and the
drill shows its chord. Off: the keyboard shows only the keys you typed, and
the chord line becomes the strokes typed so far (see `TypedStrokes`). -}
viewHintsToggle : Model -> Html Msg
viewHintsToggle model =
    if isInfoMode model.mode then
        text ""

    else
        viewOnOff "Indices clavier" model.hints ToggleHints


{-| Whether the abbreviation rule hint (affix rules, expression rules) shows:
the learner's choice once made, else on for words, sentences, the affixes and
the expressions lesson tracks, off in the other lessons. -}
abbrevHintsOn : Model -> Bool
abbrevHintsOn model =
    case model.abbrevHints of
        Just choice ->
            choice

        Nothing ->
            case model.mode of
                LessonMode ->
                    case ( model.lessons, model.selectedLesson ) of
                        ( Just (Loaded lessons), Just id ) ->
                            List.any (\l -> l.id == id && List.member l.track [ "affixes", "expressions" ]) lessons.lessons

                        _ ->
                            False

                IntroMode ->
                    False

                DefinitionMode ->
                    False

                _ ->
                    True


{-| Abbreviation rule hint on: under the chord board, the affix rules' keys and,
for the drill's current word, the short outlines the affix layer gives it
(`viewAbbreviationHints`), and the expression rules its outline uses
(`viewExpressionHints`). -}
viewAbbrevHintsToggle : Model -> Html Msg
viewAbbrevHintsToggle model =
    if isInfoMode model.mode then
        text ""

    else
        viewOnOff "Indices abr\u{00E9}viation" (abbrevHintsOn model) ToggleAbbrevHints


{-| Switches every phoneme on the page -- keys, chord board, legends, the
drill's steno and phonology -- between X-SAMPA (what the dictionary is
written in) and IPA. See `Notation`. -}
viewNotationToggle : Notation -> Html Msg
viewNotationToggle notation =
    p [ class "notation-toggle" ]
        [ text "Norme phon\u{00E9}tique : "
        , button [ onClick ToggleNotation, disabled (notation == Notation.XSampa) ] [ text "X-SAMPA" ]
        , text " "
        , button [ onClick ToggleNotation, disabled (notation == Notation.Ipa) ] [ text "IPA" ]
        ]


{-| Switches the punctuation and command chords -- the lessons' texts and drills,
the Definitions page -- between the Plover set (default) and the Pluvier one. See
`Style`. -}
viewStyleToggle : Style -> Html Msg
viewStyleToggle style =
    p [ class "notation-toggle" ]
        [ text "Ponctuation et commandes : "
        , button [ onClick ToggleStyle, disabled (style == Style.Plover) ] [ text "Plover" ]
        , text " "
        , button [ onClick ToggleStyle, disabled (style == Style.Pluvier) ] [ text "Pluvier" ]
        ]


{-| Switches the number theory -- the chiffres lessons' texts and drills, the numbers of
the Definitions page -- between Pluvier's number bar (default, the same as Plover's) and
Lapwing's numpad. See `Style.NumberStyle`. -}
viewNumberStyleToggle : NumberStyle -> Html Msg
viewNumberStyleToggle numberStyle =
    p [ class "notation-toggle" ]
        [ text "Chiffres : "
        , button [ onClick ToggleNumberStyle, disabled (numberStyle == Style.PluvierNumbers) ] [ text "Pluvier" ]
        , text " "
        , button [ onClick ToggleNumberStyle, disabled (numberStyle == Style.Lapwing) ] [ text "Lapwing" ]
        ]


viewSidebarLegends : Model -> List (Html Msg)
viewSidebarLegends model =
    case model.layout of
        Loaded layout ->
            [ Keyboard.viewLegends (simulatedKeys model) (isMarkStep model) (markKeys model layout) (currentReadingLabel model) (Notation.layout model.notation layout) ]

        _ ->
            []


{-| The extra hint under the chord board, only what affects the current word
(every word of the current sentence in sentence mode): the rules shortening it,
key names first. The words are looked up by spelling among
the affix lessons' words and in `affix-word-rules.json` (every abbreviated word),
and nothing shows for the others. -}
viewAbbreviationHints : Model -> Html Msg
viewAbbreviationHints model =
    case model.affixData of
        Nothing ->
            text ""

        Just data ->
            let
                spellings =
                    case model.drill |> Maybe.andThen Drill.currentWord of
                        Just word ->
                            if List.isEmpty word.segments then
                                [ word.ortho ]

                            else
                                List.map .text word.segments

                        Nothing ->
                            []

                found =
                    spellings
                        |> List.map (\spelling -> ( spelling, abbreviationsOf spelling data.abbreviations ))
                        |> List.filter (\( _, entries ) -> not (List.isEmpty entries))

                lessonRanks =
                    found |> List.concatMap (\( _, entries ) -> List.map .rule entries)

                ranks =
                    lessonRanks ++ List.concatMap (wordRulesOf model.wordRules) spellings

                render =
                    Notation.render model.notation
            in
            if List.isEmpty ranks then
                text ""

            else
                div [ class "abbreviation-hints" ]
                    [ Keyboard.viewAffixLegend
                        (data.rules
                            |> List.filter (\rule -> List.member rule.rank ranks)
                            |> List.map (\rule -> { rule | keyNames = List.map render rule.keyNames })
                        )
                    ]


{-| The expression rules the current item's outline uses (its `ruleRanks`: an
expressions-lesson word, or an abbreviated sentence), in the legend under the
chord board; nothing for the other items. -}
viewExpressionHints : Model -> Html Msg
viewExpressionHints model =
    case ( model.expressionData, model.drill |> Maybe.andThen Drill.currentWord ) of
        ( Just data, Just word ) ->
            let
                render =
                    Notation.render model.notation

                used =
                    data.rules
                        |> List.filter (\rule -> List.member rule.rank word.ruleRanks)
                        |> List.map (\rule -> { rule | keyNames = List.map render rule.keyNames, steno = Maybe.map render rule.steno })
            in
            if List.isEmpty used then
                text ""

            else
                div [ class "abbreviation-hints" ] [ Keyboard.viewExpressionLegend used ]

        _ ->
            text ""


{-| Sentences mode with `expression-sentences.json` loaded: switch between the
plain sentences and the same sentences written with the expression
abbreviations (the plain outline stays accepted either way). -}
viewAbbreviatedSentencesToggle : Model -> Html Msg
viewAbbreviatedSentencesToggle model =
    case ( model.mode, model.expressionSentences ) of
        ( SentenceMode, Just _ ) ->
            viewOnOff "Phrases abr\u{00E9}g\u{00E9}es" model.abbreviatedSentences ToggleAbbreviatedSentences

        _ ->
            text ""


{-| The ranks of the affix rules shortening `spelling`, from `affix-word-rules.json`
(every abbreviated word, not only the lessons' words); empty when unknown. -}
wordRulesOf : Dict String (List Int) -> String -> List Int
wordRulesOf wordRules spelling =
    Dict.get (String.toLower (String.trim spelling)) wordRules |> Maybe.withDefault []


abbreviationsOf : String -> List Lessons.Abbreviation -> List Lessons.Abbreviation
abbreviationsOf spelling =
    let
        key =
            String.toLower (String.trim spelling)
    in
    List.filter (\entry -> String.toLower entry.ortho == key)


viewTrainer : Model -> Html Msg
viewTrainer model =
    div []
        [ case ( model.mode, activeItems model ) of
            ( IntroMode, _ ) ->
                viewIntroPage

            ( DefinitionMode, _ ) ->
                viewDefinitions model

            ( LessonMode, _ ) ->
                viewLessons model

            ( _, Just (Failed message) ) ->
                p [ class "error" ] [ text ("Couldn't load practice " ++ modeNoun model.mode ++ ": " ++ message) ]

            ( _, Just (Loaded _) ) ->
                div []
                    [ p [ class "word-nav-row" ] [ viewWordNav model.mode ]
                    , viewDrill model
                    ]

            _ ->
                p [] [ text ("Loading practice " ++ modeNoun model.mode ++ "...") ]
        , if model.mode == IntroMode || (model.mode == LessonMode && model.drill == Nothing) then
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
                    div [ classList [ ( "sim-mark", isMarkStep model ) ] ]
                        [ if model.drill /= Nothing && not (isInfoMode model.mode) then
                            p [ class "simulate-row" ] [ button [ onClick StartSimulation ] [ text "Simulate" ] ]

                          else
                            text ""
                        , Keyboard.view
                            (if model.simulation /= Nothing then
                                { highlighted = simulatedKeys model, correct = Just True }

                             else if model.hints && not (isInfoMode model.mode) && (model.drill |> Maybe.andThen .feedback) == Just False then
                                -- A wrong press: the keys actually pressed, in red.
                                { highlighted = model.lastStroke, correct = Just False }

                             else if model.hints && not (isInfoMode model.mode) then
                                -- A hint is the expected stroke, not a press: always gray (the
                                -- previous word's lingering feedback must not turn it green/red).
                                { highlighted = model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty
                                , correct = Nothing
                                }

                             else
                                { highlighted = model.lastStroke
                                , correct = model.drill |> Maybe.andThen .feedback
                                }
                            )
                            layout.keys
                        , Keyboard.viewChordBoard (simulatedKeys model) (hintKeys model) (pairAllowed model loadedLayout) layout
                        , Keyboard.viewStrokeLegend (simulatedKeys model) (hintKeys model) (strokeInPhonology model loadedLayout) layout
                        , if abbrevHintsOn model && not (isInfoMode model.mode) then
                            div []
                                [ viewAbbreviationHints model
                                , viewExpressionHints model
                                ]

                          else
                            text ""
                        ]
        ]


modeNoun : Mode -> String
modeNoun mode =
    case mode of
        WordMode ->
            "words"

        SentenceMode ->
            "sentences"

        IntroMode ->
            "introduction"

        DefinitionMode ->
            "definitions"

        LessonMode ->
            "lessons"


loadedKeys : LoadState Layout -> List KeyInfo
loadedKeys layout =
    case layout of
        Loaded loaded ->
            loaded.keys

        _ ->
            []


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
                Definitions.view (Notation.render model.notation)
                    SimulateOutline
                    model.abbreviations
                    model.expressionDefinitions
                    ((model.punctuationData |> Maybe.map (Lessons.punctuationEntries model.style) |> Maybe.withDefault [])
                        ++ (model.numberData |> Maybe.map (Lessons.numberEntries model.numberStyle) |> Maybe.withDefault [])
                        ++ (model.spellingData |> Maybe.map Lessons.spellingEntries |> Maybe.withDefault [])
                    )
                    model.numberStyle
                    model.query
                    definitions

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
                            , title = Lessons.displayTitle (Notation.render model.notation) lessons lesson
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
                            [ p [ class "lesson-back lesson-back-drill" ]
                                ([ button [ onClick BackToLessonList ] [ text "← Lessons" ]
                                 , text " "
                                 , button [ onClick (SelectLesson lesson.id) ] [ text "← Lesson text" ]
                                 , text " "
                                 , button [ onClick ToggleLessonMix ]
                                    [ text
                                        (if model.lessonMix then
                                            "Current mix 50% old - 50% new"

                                         else
                                            "Current mix 100% new"
                                        )
                                    ]
                                 ]
                                    ++ Lessons.viewPrevNext onPrev onNext
                                    ++ [ viewWordNav model.mode ]
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


{-| After the lit stroke `step` of `strokes` has been shown long enough, move to
the next one (`SimulationStep`; past the last one it ends the run): 1 s plus
0.2 s per key pressed for an intermediate stroke, 3 s for the last one (so 3 s
for a single-stroke word). -}
simulationTimer : Int -> Int -> List (List Int) -> Cmd Msg
simulationTimer run step strokes =
    let
        milliseconds =
            if step >= List.length strokes - 1 then
                3000

            else
                1000 + 200 * (List.drop step strokes |> List.head |> Maybe.map List.length |> Maybe.withDefault 0)
    in
    Process.sleep (toFloat milliseconds) |> Task.perform (\_ -> SimulationStep run (step + 1))


{-| The strokes the Simulate button lights for the current item: the word's
outline, or, in a sentence, the current word's slice of it. -}
currentStrokes : Model -> List (List Int)
currentStrokes model =
    case model.drill of
        Just drill ->
            case Drill.currentWord drill of
                Just word ->
                    word.strokes

                Nothing ->
                    []

        Nothing ->
            []


{-| Where the Simulate run's lit stroke sits in its word: 0 for a word's first
stroke. A sentence is simulated whole, so this restarts at each word. -}
simulationOffsetInWord : Model -> Int
simulationOffsetInWord model =
    case ( model.simulation, model.drill |> Maybe.andThen Drill.currentWord ) of
        ( Just simulation, Just word ) ->
            Tuple.second (strokePosition word simulation.step)

        ( Just simulation, Nothing ) ->
            simulation.step

        _ ->
            0


{-| A stroke index of a sentence as (the word's index, the stroke's index within
that word); a lone word is word 0. -}
strokePosition : PracticeWord -> Int -> ( Int, Int )
strokePosition word absolute =
    if List.isEmpty word.segments then
        ( 0, absolute )

    else
        word.segments
            |> List.foldl
                (\segment ( index, remaining, found ) ->
                    case found of
                        Just _ ->
                            ( index, remaining, found )

                        Nothing ->
                            if remaining < segment.strokeCount then
                                ( index, remaining, Just ( index, remaining ) )

                            else
                                ( index + 1, remaining - segment.strokeCount, Nothing )
                )
                ( 0, absolute, Nothing )
            |> (\( index, remaining, found ) -> Maybe.withDefault ( index - 1, remaining ) found)


{-| Whether the item is shown as a sentence, word by word: every Sentences item, and the
phrases of the punctuation lessons (they carry segments). -}
isSegmented : Model -> PracticeWord -> Bool
isSegmented model word =
    model.mode == SentenceMode || not (List.isEmpty word.segments)


{-| The word of a sentence being shown: the one the Simulate run is in while it
runs, else the one the drill is at. -}
shownSegment : Model -> Drill.State -> PracticeWord -> Int
shownSegment model drill word =
    case model.simulation of
        Just simulation ->
            Tuple.first (strokePosition word simulation.step)

        Nothing ->
            Drill.currentSegmentIndex drill


{-| The Simulate button lights a conjugation marker's stroke (after the first
stroke of the word) yellow instead of green. -}
isMarkStep : Model -> Bool
isMarkStep model =
    case ( model.simulation, model.layout ) of
        ( Just simulation, Loaded layout ) ->
            simulationOffsetInWord model > 0
                && (List.drop simulation.step simulation.strokes
                        |> List.head
                        |> Maybe.map (Keyboard.isConjugationStroke layout)
                        |> Maybe.withDefault False
                   )

        _ ->
            False


{-| The conjugation marker stroke being highlighted, if any: the Simulate
button's lit one, or (hints on, no wrong press showing) the one the drill expects
next after the word's first stroke. Its legend line gets its features in bold. -}
markKeys : Model -> Layout -> Set.Set Int
markKeys model layout =
    case model.simulation of
        Just _ ->
            if isMarkStep model then
                simulatedKeys model

            else
                Set.empty

        Nothing ->
            case model.drill of
                Just drill ->
                    if model.hints && drill.feedback /= Just False && drill.currentStrokeIndex > 0 then
                        case Drill.expectedStroke drill of
                            Just keys ->
                                if Keyboard.isConjugationStroke layout (Set.toList keys) then
                                    keys

                                else
                                    Set.empty

                            Nothing ->
                                Set.empty

                    else
                        Set.empty

                Nothing ->
                    Set.empty


{-| The stroke the hint shows (the gray keys): the drill's expected one, with hints
on, outside a Simulate run and while no wrong press is showing in red. The chord
board and the 3-/4-key groups gray the phonemes of the word it composes. -}
hintKeys : Model -> Set.Set Int
hintKeys model =
    if model.hints && model.simulation == Nothing && not (isInfoMode model.mode) && (model.drill |> Maybe.andThen .feedback) /= Just False then
        model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty

    else
        Set.empty


{-| Whether a 2-key badge may light in the Simulate run. A 2-key stroke always
lights its own badge; a 3-/4-key stroke ("2", "5", "1") contains several pairs
(y, u, E...) that must stay dark unless the word's phonology has that phoneme. -}
pairAllowed : Model -> Layout -> Set.Set Int -> List Int -> Bool
pairAllowed model rawLayout strokeKeys pair =
    if Set.size strokeKeys <= 2 then
        True

    else
        let
            phonology =
                currentPhonology model
        in
        rawLayout.phonemeLayers
            |> List.filter (\l -> l.keyCount == 2)
            |> List.concatMap .strokes
            |> List.filter (\stroke -> Set.fromList stroke.keys == Set.fromList pair)
            |> List.any (\stroke -> List.any (\c -> String.contains (String.fromChar c) phonology) (String.toList stroke.phonemes))


{-| Whether the stroke of this 3-/4-key group ("2", "5", "1") may light in the
Simulate run: its phoneme must be in the word's phonology (the four thumb keys
of "@aie" hold "2" and "5" too, which the word does not write). -}
strokeInPhonology : Model -> Layout -> Set.Set Int -> List Int -> Bool
strokeInPhonology model rawLayout _ keys =
    let
        phonology =
            currentPhonology model
    in
    rawLayout.phonemeLayers
        |> List.filter (\l -> l.keyCount > 2)
        |> List.concatMap .strokes
        |> List.filter (\stroke -> Set.fromList stroke.keys == Set.fromList keys)
        |> List.any (\stroke -> List.any (\c -> String.contains (String.fromChar c) phonology) (String.toList stroke.phonemes))


{-| The (raw X-SAMPA) phonology of the word (sentence mode: the current word) being drilled. -}
currentPhonology : Model -> String
currentPhonology model =
    case ( model.mode, model.simulation ) of
        ( DefinitionMode, Just simulation ) ->
            simulation.phonology

        _ ->
            drillPhonology model


drillPhonology : Model -> String
drillPhonology model =
    case model.drill of
        Just drill ->
            case Drill.currentWord drill of
                Just word ->
                    if isSegmented model word then
                        String.split " " word.phonology |> List.drop (shownSegment model drill word) |> List.head |> Maybe.withDefault ""

                    else
                        word.phonology

                Nothing ->
                    ""

        Nothing ->
            ""


{-| The stroke of the current word's chord line to put in bold: the one the
Simulate run lights, else the next one to type. In a sentence the index counts
from the sentence's first stroke. -}
workingStroke : Model -> Drill.State -> PracticeWord -> Int
workingStroke model drill word =
    case model.simulation of
        Just simulation ->
            simulation.step

        Nothing ->
            drill.currentStrokeIndex


{-| What of the reading label the highlighted conjugation marker stands for. -}
labelEmphasis : Model -> List String
labelEmphasis model =
    case model.layout of
        Loaded layout ->
            Keyboard.markerPatterns layout (markKeys model layout) (currentReadingLabel model)

        _ ->
            []


{-| `label` with each occurrence of one of `patterns` (at the start or after a
space) in bold. -}
emphasize : List String -> String -> List (Html Msg)
emphasize patterns label =
    let
        -- The earliest (index, pattern) occurrence starting a word.
        firstHit =
            patterns
                |> List.filterMap
                    (\pattern ->
                        String.indexes pattern label
                            |> List.filter (\i -> i == 0 || String.slice (i - 1) i label == " ")
                            |> List.head
                            |> Maybe.map (\i -> ( i, pattern ))
                    )
                |> List.sortBy Tuple.first
                |> List.head
    in
    case firstHit of
        Just ( i, pattern ) ->
            text (String.left i label)
                :: Html.span [ class "legend-feature" ] [ text pattern ]
                :: emphasize patterns (String.dropLeft (i + String.length pattern) label)

        Nothing ->
            [ text label ]


{-| The reading label of the word (sentence mode: of the current word) being drilled. -}
currentReadingLabel : Model -> String
currentReadingLabel model =
    case model.drill of
        Just drill ->
            case Drill.currentWord drill of
                Just word ->
                    if isSegmented model word then
                        word.segments |> List.drop (shownSegment model drill word) |> List.head |> Maybe.map .label |> Maybe.withDefault ""

                    else
                        word.label

                Nothing ->
                    ""

        Nothing ->
            ""


{-| The keys of the stroke the Simulate button currently lights, if it runs. -}
simulatedKeys : Model -> Set.Set Int
simulatedKeys model =
    model.simulation
        |> Maybe.andThen (\simulation -> List.drop simulation.step simulation.strokes |> List.head)
        |> Maybe.map Set.fromList
        |> Maybe.withDefault Set.empty


{-| "Previous word" / "Next word": step the current drill, in every mode,
pushed to the right of its row. -}
viewWordNav : Mode -> Html Msg
viewWordNav mode =
    let
        noun =
            if mode == SentenceMode then
                "sentence"

            else
                "word"
    in
    span [ class "word-nav" ]
        [ button [ onClick (SkipWords -1) ] [ text ("← Previous " ++ noun) ]
        , text " "
        , button [ onClick (SkipWords 1) ] [ text ("Next " ++ noun ++ " →") ]
        ]


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
            if isSegmented model word then
                viewSentence chordDisplay (labelEmphasis model) (shownSegment model drill word) (workingStroke model drill word) word

            else
                div [ class "drill" ]
                    [ div [ class "drill-words" ]
                        [ div [ class "current-word" ]
                            (p [ class "target-word" ] (viewInContext word)
                                :: viewReading chordDisplay (labelEmphasis model) (workingStroke model drill word) word.label word.phonology word.steno word.strokes
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
viewSentence : ChordDisplay -> List String -> Int -> Int -> PracticeWord -> Html Msg
viewSentence chordDisplay emphasis currentIndex strokeIndex sentence =
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
            if index == 0 || not segment.spaceBefore || String.startsWith "-" segment.text then
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

        -- A punctuation lesson's phrase carries its marks as segments already.
        lastSegmentEnds c =
            sentence.segments |> List.reverse |> List.head |> Maybe.map (\segment -> String.endsWith c segment.text) |> Maybe.withDefault False

        finalPunctuation =
            String.right 1 sentence.ortho
                |> (\c ->
                        if String.contains c ".?!" && not (lastSegmentEnds c) then
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
                                emphasis
                                (strokeIndex - segmentStart currentIndex)
                                segment.label
                                (String.split " " sentence.phonology |> List.drop currentIndex |> List.head |> Maybe.withDefault "")
                                segment.steno
                                (sentence.strokes |> List.drop (segmentStart currentIndex) |> List.take segment.strokeCount)

                        Nothing ->
                            []
                   )
            )
        ]


{-| The pronunciation between slashes; a mark or a command has none. -}
phonologyLine : String -> String
phonologyLine phonology =
    if String.isEmpty phonology then
        "\u{00A0}"

    else
        "/" ++ phonology ++ "/"


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
viewReading : ChordDisplay -> List String -> Int -> String -> String -> String -> List (List Int) -> List (Html Msg)
viewReading chordDisplay emphasis currentStroke label phonology steno strokes =
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
                        |> List.indexedMap (\i ( text_, stroke ) -> ( i, text_, stroke ))

                -- Each stroke its own span, the one being worked on in bold.
                strokeSpans parts =
                    parts
                        |> List.map
                            (\( i, text_, _ ) ->
                                Html.span [ classList [ ( "current-stroke", i == currentStroke ) ] ] [ text (Notation.render notation text_) ]
                            )
                        |> List.intersperse (text "/")

                baseParts =
                    strokeParts |> List.filter (\( _, _, stroke ) -> not (isMarkStroke stroke))

                markParts =
                    strokeParts |> List.filter (\( _, _, stroke ) -> isMarkStroke stroke)

                markPart =
                    markParts |> List.map (\( _, text_, _ ) -> text_) |> String.join "/"
            in
            [ p [ class "target-label" ] (emphasize emphasis label)
            , p [ class "target-phonology" ] [ text (phonologyLine (Notation.render notation phonology)) ]
            , p [ class "target-steno" ] (strokeSpans baseParts)
            , p [ class "target-mark" ]
                (if String.isEmpty markPart then
                    [ text "\u{00A0}" ]

                 else
                    strokeSpans markParts
                )
            ]

        ShowTyped notation typed ->
            [ p [ class "target-label" ] (emphasize emphasis label)
            , p [ class "target-phonology" ] [ text (phonologyLine (Notation.render notation phonology)) ]
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
