module Drill exposing (PracticeWord, Segment, State, applyStroke, currentSegmentIndex, currentWord, decoder, expectedStroke, init, nextWord, reshuffle, sentenceDecoder)

{-| The drill engine: a shuffled walk through the word list (loaded already
frequency-ordered by `util/export_practice_words.py`, but drilled in a
random pass order instead), with no repeats until every word in the list has
come up once, then reshuffled for the next pass. No persistence, no timing,
no adaptive ordering -- refreshing the page always restarts at word 0 of a
fresh shuffle, by design (see the plan's MVP scope). The shuffle itself
needs `Cmd`/`Random`, which this module deliberately has no access to (kept
pure, like the rest of the state machine) -- `Main.elm` generates the
shuffled order and hands it to `init`/`reshuffle`.
-}

import Array exposing (Array)
import Json.Decode as D
import Set exposing (Set)


{-| One drill item: a word's spelling plus ONE of its chords. A self-homograph
spelling ("calmez" = impératif / indicatif présent) has several independently
valid chords and so several items, told apart by `label` -- the grammatical
reading(s) that item's chord writes (see `util/export_practice_words.py`).

A practice sentence is the same shape -- `ortho` its text, `strokes` all its
words' strokes in order -- plus one `Segment` per word, so the view can say
which word the next stroke belongs to (see `sentenceDecoder`). A single
word has no segments. -}
type alias PracticeWord =
    { ortho : String
    , label : String
    , phonology : String
    , steno : String
    , strokes : List (List Int)
    , segments : List Segment
    }


{-| One word of a practice sentence: its text as written there, the reading
it has in context, its chord, and how many of the sentence's strokes it takes
(see `util/export_practice_sentences.py`). -}
type alias Segment =
    { text : String
    , label : String
    , steno : String
    , strokeCount : Int
    }


wordDecoder : D.Decoder PracticeWord
wordDecoder =
    D.map6 PracticeWord
        (D.field "ortho" D.string)
        (D.field "label" D.string)
        (D.field "phonology" D.string)
        (D.field "steno" D.string)
        (D.field "strokes" (D.list (D.list D.int)))
        (D.succeed [])


decoder : D.Decoder (List PracticeWord)
decoder =
    D.list wordDecoder


segmentDecoder : D.Decoder Segment
segmentDecoder =
    D.map4 Segment
        (D.field "text" D.string)
        (D.field "label" D.string)
        (D.field "steno" D.string)
        (D.field "strokeCount" D.int)


sentenceDecoder : D.Decoder (List PracticeWord)
sentenceDecoder =
    D.list
        (D.map6 PracticeWord
            (D.field "text" D.string)
            (D.succeed "")
            (D.field "phonology" D.string)
            (D.field "steno" D.string)
            (D.field "strokes" (D.list (D.list D.int)))
            (D.field "words" (D.list segmentDecoder))
        )


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


{-| Swap in a freshly-shuffled word order (a new pass), restarting at word 0.
`Main.elm` calls this once at load (after `GotWords`/`ShuffledWords`) and
again each time `applyStroke`'s `passCompleted` flag comes back `True`. -}
reshuffle : List PracticeWord -> State -> State
reshuffle words state =
    { state
        | words = Array.fromList words
        , currentWordIndex = 0
        , currentStrokeIndex = 0
    }


currentWord : State -> Maybe PracticeWord
currentWord state =
    Array.get state.currentWordIndex state.words


{-| The word that will become current after this one, wrapping to the start
of the (current) pass -- purely a preview; advancing the drill itself is
still `applyStroke`'s job, and a pass boundary reshuffles before this word is
ever reached. -}
nextWord : State -> Maybe PracticeWord
nextWord state =
    Array.get (wrappedIndex state (state.currentWordIndex + 1)) state.words


wrappedIndex : State -> Int -> Int
wrappedIndex state index =
    modBy (max 1 (Array.length state.words)) index


{-| Which of the current sentence's words the next expected stroke belongs to
(0 for a single word, which has no segments). -}
currentSegmentIndex : State -> Int
currentSegmentIndex state =
    currentWord state
        |> Maybe.map
            (\word ->
                word.segments
                    |> List.foldl
                        (\segment ( index, strokesBefore, found ) ->
                            case found of
                                Just _ ->
                                    ( index, strokesBefore, found )

                                Nothing ->
                                    if state.currentStrokeIndex < strokesBefore + segment.strokeCount then
                                        ( index, strokesBefore, Just index )

                                    else
                                        ( index + 1, strokesBefore + segment.strokeCount, Nothing )
                        )
                        ( 0, 0, Nothing )
                    |> (\( _, _, found ) -> Maybe.withDefault 0 found)
            )
        |> Maybe.withDefault 0


expectedStroke : State -> Maybe (Set Int)
expectedStroke state =
    currentWord state
        |> Maybe.andThen (\word -> List.drop state.currentStrokeIndex word.strokes |> List.head)
        |> Maybe.map Set.fromList


{-| Advance the drill on a decoded stroke: match -> flash correct, move to the
next stroke (or the next word, wrapping, if that was the word's last stroke);
no match -> flash incorrect, retry the same word/stroke. No counter, no
penalty, no lockout -- deliberately bare minimum.

Returns whether this stroke completed the last word of the current pass (the
index wrapped back to 0), so `Main.elm` knows to generate a new shuffle --
this module has no `Cmd`/`Random` access of its own, so it only reports the
boundary rather than acting on it.
-}
applyStroke : Set Int -> State -> ( State, Bool )
applyStroke observed state =
    case ( currentWord state, expectedStroke state ) of
        ( Just word, Just expected ) ->
            if observed == expected then
                if state.currentStrokeIndex + 1 >= List.length word.strokes then
                    let
                        newIndex =
                            wrappedIndex state (state.currentWordIndex + 1)
                    in
                    ( { state
                        | currentWordIndex = newIndex
                        , currentStrokeIndex = 0
                        , feedback = Just True
                      }
                    , newIndex == 0
                    )

                else
                    ( { state
                        | currentStrokeIndex = state.currentStrokeIndex + 1
                        , feedback = Just True
                      }
                    , False
                    )

            else
                ( { state | feedback = Just False }, False )

        _ ->
            ( state, False )
