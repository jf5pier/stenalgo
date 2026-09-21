module Drill exposing (PracticeWord, State, applyStroke, currentWord, decoder, expectedStroke, init)

{-| The bare-minimum drill engine: a sequential walk through the
frequency-ordered word list (already sorted by `util/export_practice_words.py`),
wrapping at the end. No persistence, no timing, no adaptive ordering -- refreshing
the page always restarts at word 0, by design (see the plan's MVP scope).
-}

import Array exposing (Array)
import Json.Decode as D
import Set exposing (Set)


type alias PracticeWord =
    { ortho : String
    , steno : String
    , strokes : List (List Int)
    , frequency : Float
    }


wordDecoder : D.Decoder PracticeWord
wordDecoder =
    D.map4 PracticeWord
        (D.field "ortho" D.string)
        (D.field "steno" D.string)
        (D.field "strokes" (D.list (D.list D.int)))
        (D.field "frequency" D.float)


decoder : D.Decoder (List PracticeWord)
decoder =
    D.list wordDecoder


type alias State =
    { words : Array PracticeWord
    , currentWordIndex : Int
    , currentStrokeIndex : Int
    , feedback : Maybe Bool
    }


init : List PracticeWord -> State
init words =
    { words = Array.fromList words
    , currentWordIndex = 0
    , currentStrokeIndex = 0
    , feedback = Nothing
    }


currentWord : State -> Maybe PracticeWord
currentWord state =
    Array.get state.currentWordIndex state.words


expectedStroke : State -> Maybe (Set Int)
expectedStroke state =
    currentWord state
        |> Maybe.andThen (\word -> List.drop state.currentStrokeIndex word.strokes |> List.head)
        |> Maybe.map Set.fromList


{-| Advance the drill on a decoded stroke: match -> flash correct, move to the
next stroke (or the next word, wrapping, if that was the word's last stroke);
no match -> flash incorrect, retry the same word/stroke. No counter, no
penalty, no lockout -- deliberately bare minimum.
-}
applyStroke : Set Int -> State -> State
applyStroke observed state =
    case ( currentWord state, expectedStroke state ) of
        ( Just word, Just expected ) ->
            if observed == expected then
                if state.currentStrokeIndex + 1 >= List.length word.strokes then
                    { state
                        | currentWordIndex = modBy (max 1 (Array.length state.words)) (state.currentWordIndex + 1)
                        , currentStrokeIndex = 0
                        , feedback = Just True
                    }

                else
                    { state
                        | currentStrokeIndex = state.currentStrokeIndex + 1
                        , feedback = Just True
                    }

            else
                { state | feedback = Just False }

        _ ->
            state
