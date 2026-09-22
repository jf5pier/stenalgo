module Main exposing (main)

import Browser
import Dict exposing (Dict)
import Drill exposing (PracticeWord)
import GeminiPr
import Html exposing (Html, button, div, h1, p, text)
import Html.Attributes exposing (class, disabled)
import Html.Events exposing (onClick)
import Http
import Json.Decode as D
import Keyboard exposing (KeyInfo, Layout)
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
state machine -- a sentence is just one long multi-stroke item. -}
type Mode
    = WordMode
    | SentenceMode


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

            else
                startDrillIfIdle { model | mode = mode, drill = Nothing }

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
            case ( GeminiPr.decodePacket bytes, model.drill ) of
                ( Ok labels, Just drill ) ->
                    let
                        observed =
                            labels
                                |> List.filterMap (\label -> Dict.get label model.keymap)
                                |> Set.fromList

                        ( newDrill, passCompleted ) =
                            Drill.applyStroke observed drill

                        shuffleCmd =
                            if passCompleted then
                                case activeItems model of
                                    Loaded words ->
                                        Random.generate ShuffledWords (shuffleGenerator words)

                                    _ ->
                                        Cmd.none

                            else
                                Cmd.none
                    in
                    ( { model | drill = Just newDrill }, shuffleCmd )

                _ ->
                    -- Malformed packet, or the word list hasn't loaded yet -- ignore.
                    ( model, Cmd.none )


activeItems : Model -> LoadState (List PracticeWord)
activeItems model =
    case model.mode of
        WordMode ->
            model.words

        SentenceMode ->
            model.sentences


{-| Shuffle the current mode's list into a fresh drill, once it has loaded
and unless a drill is already running. -}
startDrillIfIdle : Model -> ( Model, Cmd Msg )
startDrillIfIdle model =
    case ( model.drill, activeItems model ) of
        ( Nothing, Loaded items ) ->
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
    p [ class "mode-switch" ] [ modeButton WordMode "Words", text " ", modeButton SentenceMode "Sentences" ]


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
            [ Keyboard.viewLegends (Notation.layout model.notation layout) ]

        _ ->
            []


viewTrainer : Model -> Html Msg
viewTrainer model =
    div []
        [ case activeItems model of
            Failed message ->
                p [ class "error" ] [ text ("Couldn't load practice " ++ modeNoun model.mode ++ ": " ++ message) ]

            Loading ->
                p [] [ text ("Loading practice " ++ modeNoun model.mode ++ "...") ]

            Loaded _ ->
                viewDrill model
        , case model.layout of
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
                        { highlighted = model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty
                        , correct = model.drill |> Maybe.andThen .feedback
                        }
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
            in
            case model.mode of
                WordMode ->
                    div [ class "drill" ]
                        [ div [ class "drill-words" ]
                            [ div [ class "current-word" ]
                                (p [ class "target-word" ] [ text word.ortho ]
                                    :: viewReading model.notation reservedKeys word.label word.phonology word.steno word.strokes
                                )
                            , p [ class "next-word" ]
                                [ text (Drill.nextWord drill |> Maybe.map .ortho |> Maybe.withDefault "\u{00A0}") ]
                            ]
                        ]

                SentenceMode ->
                    viewSentence model.notation reservedKeys (Drill.currentSegmentIndex drill) word

        _ ->
            p [] [ text "Nothing to practice." ]


{-| A sentence with its current word highlighted (words already written
dimmed), and that word's reading/phonology/chord underneath -- the whole
sentence's chords at once would be unreadable. `phonology` holds one
space-separated transcription per word, parallel to `segments`. -}
viewSentence : Notation -> Set.Set Int -> Int -> PracticeWord -> Html Msg
viewSentence notation reservedKeys currentIndex sentence =
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
                            viewReading notation
                                reservedKeys
                                segment.label
                                (String.split " " sentence.phonology |> List.drop currentIndex |> List.head |> Maybe.withDefault "")
                                segment.steno
                                (sentence.strokes |> List.drop (segmentStart currentIndex) |> List.take segment.strokeCount)

                        Nothing ->
                            []
                   )
            )
        ]


{-| One word's reading label, phonology and chord. Reserved keys (`*`, `#`,
and the two still-unassigned ones) never carry a phoneme -- a stroke made up
only of those is the `*`/`#` track's trailing mark, which picks which *lemma*
you mean among homophones of different words (`src/ambiguitychecker.py`'s
"lemma-homophone ambiguity", e.g. a/à/as), not a conjugated form of one lemma
(that's Phase P's separate mechanism, an extra stroke of ordinary coda keys --
see the sidebar's "Conjugation markers" legend). Split onto its own line
under the chord, always rendered (even empty) so a word that has one doesn't
shift the layout of the one after it.
-}
viewReading : Notation -> Set.Set Int -> String -> String -> String -> List (List Int) -> List (Html Msg)
viewReading notation reservedKeys label phonology steno strokes =
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
    , p [ class "target-mark" ]
        [ text
            (if String.isEmpty markPart then
                "\u{00A0}"

             else
                markPart
            )
        ]
    ]
