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
import Keyboard exposing (KeyInfo)
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
    { layout : LoadState (List KeyInfo)
    , words : LoadState (List PracticeWord)
    , drill : Maybe Drill.State
    , keymap : Dict String Int
    , serial : SerialStatus
    }


type Msg
    = GotLayout (Result Http.Error (List KeyInfo))
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
        GotLayout (Ok keys) ->
            ( { model | layout = Loaded keys, keymap = Keyboard.geminiKeymap keys }, Cmd.none )

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


view : Model -> Html Msg
view model =
    div [ class "app" ]
        [ h1 [] [ text "Stenalgo practice" ]
        , case model.serial of
            Unsupported ->
                p [ class "unsupported" ]
                    [ text "This browser doesn't support the Web Serial API. Use Chrome or Edge to practice with real hardware." ]

            _ ->
                viewTrainer model
        ]


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

            Loaded keys ->
                Keyboard.view
                    { highlighted = model.drill |> Maybe.andThen Drill.expectedStroke |> Maybe.withDefault Set.empty
                    , correct = model.drill |> Maybe.andThen .feedback
                    }
                    keys
        ]


viewDrill : Model -> Html Msg
viewDrill model =
    case model.drill |> Maybe.andThen Drill.currentWord of
        Just word ->
            div [ class "drill" ]
                [ p [ class "target-word" ] [ text word.ortho ]
                , p [ class "target-steno" ] [ text word.steno ]
                ]

        Nothing ->
            p [] [ text "No words to practice." ]
