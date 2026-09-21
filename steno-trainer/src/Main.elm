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
import Ports
import Set


type LoadState a
    = Loading
    | Loaded a
    | Failed String


type SerialStatus
    = CheckingSupport
    | Unsupported
    | Disconnected
    | Connected


type alias Model =
    { layout : LoadState Layout
    , words : LoadState (List PracticeWord)
    , drill : Maybe Drill.State
    , keymap : Dict String Int
    , serial : SerialStatus
    }


type Msg
    = GotLayout (Result Http.Error Layout)
    | GotWords (Result Http.Error (List PracticeWord))
    | ClickConnect
    | SerialStatusChanged String
    | IncomingBytes (List Int)


main : Program () Model Msg
main =
    Browser.element { init = init, update = update, subscriptions = subscriptions, view = view }


init : () -> ( Model, Cmd Msg )
init _ =
    ( { layout = Loading
      , words = Loading
      , drill = Nothing
      , keymap = Dict.empty
      , serial = CheckingSupport
      }
    , Cmd.batch
        [ Http.get { url = "public/data/keyboard-layout.json", expect = Http.expectJson GotLayout Keyboard.decoder }
        , Http.get { url = "public/data/practice-words.json", expect = Http.expectJson GotWords Drill.decoder }
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
            ( { model | words = Loaded words, drill = Just (Drill.init words) }, Cmd.none )

        GotWords (Err err) ->
            ( { model | words = Failed (httpErrorToString err) }, Cmd.none )

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
                    in
                    ( { model | drill = Just (Drill.applyStroke observed drill) }, Cmd.none )

                _ ->
                    -- Malformed packet, or the word list hasn't loaded yet -- ignore.
                    ( model, Cmd.none )


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


{-| Two columns: a narrow left sidebar carrying the title and the two
plain-text legends (too easy to lose below the tall keyboards otherwise), and
the actual trainer -- connect button, drill, interactive keyboard, second
chord-layer keyboard -- to its right.
-}
view : Model -> Html Msg
view model =
    div [ class "app" ]
        [ div [ class "sidebar" ] (h1 [] [ text "Stenalgo practice" ] :: viewSidebarLegends model)
        , div [ class "main" ]
            [ case model.serial of
                Unsupported ->
                    p [ class "unsupported" ]
                        [ text "This browser doesn't support the Web Serial API. Use Chrome or Edge to practice with real hardware." ]

                _ ->
                    viewTrainer model
            ]
        ]


viewSidebarLegends : Model -> List (Html Msg)
viewSidebarLegends model =
    case model.layout of
        Loaded layout ->
            [ Keyboard.viewLegends layout ]

        _ ->
            []


viewTrainer : Model -> Html Msg
viewTrainer model =
    div []
        [ button
            [ onClick ClickConnect, disabled (model.serial == Connected) ]
            [ text
                (if model.serial == Connected then
                    "Connected"

                 else
                    "Connect steno machine"
                )
            ]
        , case model.words of
            Failed message ->
                p [ class "error" ] [ text ("Couldn't load practice words: " ++ message) ]

            Loading ->
                p [] [ text "Loading practice words..." ]

            Loaded _ ->
                viewDrill model
        , case model.layout of
            Failed message ->
                p [ class "error" ] [ text ("Couldn't load keyboard layout: " ++ message) ]

            Loading ->
                p [] [ text "Loading keyboard layout..." ]

            Loaded layout ->
                div []
                    [ Keyboard.view
                        { highlighted = model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty
                        , correct = model.drill |> Maybe.andThen .feedback
                        }
                        layout.keys
                    , Keyboard.viewChordBoard layout
                    ]
        ]


{-| Reserved keys (`*`, `#`, and the two still-unassigned ones) never carry a
phoneme -- a stroke made up only of those is the `*`/`#` track's trailing
mark, which picks which *lemma* you mean among homophones of different words
(`src/ambiguitychecker.py`'s "lemma-homophone ambiguity", e.g. a/à/as), not a
conjugated form of one lemma (that's Phase P's separate mechanism, an extra
stroke of ordinary coda keys -- see the sidebar's "Conjugation markers"
legend). Split onto its own line under the word, always rendered (even
empty) so a word that has one doesn't shift the layout of the one after it.
-}
viewDrill : Model -> Html Msg
viewDrill model =
    case model.drill |> Maybe.andThen Drill.currentWord of
        Just word ->
            let
                reservedKeys =
                    case model.layout of
                        Loaded layout ->
                            layout.keys |> List.filter .reserved |> List.map .index |> Set.fromList

                        _ ->
                            Set.empty

                isMarkStroke stroke =
                    not (List.isEmpty stroke) && List.all (\k -> Set.member k reservedKeys) stroke

                strokeParts =
                    List.map2 Tuple.pair (String.split "/" word.steno) word.strokes

                basePart =
                    strokeParts |> List.filter (\( _, stroke ) -> not (isMarkStroke stroke)) |> List.map Tuple.first |> String.join "/"

                markPart =
                    strokeParts |> List.filter (\( _, stroke ) -> isMarkStroke stroke) |> List.map Tuple.first |> String.join "/"
            in
            div [ class "drill" ]
                [ p [ class "target-word" ] [ text word.ortho ]
                , p [ class "target-steno" ] [ text basePart ]
                , p [ class "target-mark" ]
                    [ text
                        (if String.isEmpty markPart then
                            "\u{00A0}"

                         else
                            markPart
                        )
                    ]
                ]

        Nothing ->
            p [] [ text "No words to practice." ]
