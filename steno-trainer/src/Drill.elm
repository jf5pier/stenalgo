module Drill exposing (TextStatus(..), textStatus, applyText, Outline, PracticeWord, Segment, State, applyStroke, currentSegmentIndex, currentWord, decoder, skipWords, matchedOutline, expectedStroke, init, nextWord, reshuffle, sentenceDecoder, wordDecoder)

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
import Json.Decode.Pipeline exposing (hardcoded, optional, required)
import Set exposing (Set)


{-| One drill item: a word's spelling plus ONE of its chords. A self-homograph
spelling ("calmez" = impératif / indicatif présent) has several independently
valid chords and so several items, told apart by `label` -- the grammatical
reading(s) that item's chord writes (see `util/export_practice_words.py`),
and `before`/`after` the context words shown around it for that reading
("la", "que tu", "!") -- display only, never typed.

A punctuation lesson's phrase ("Oh !", `segments` with the marks as their own
segments, `spaceBefore` false where a mark attaches to its neighbour) is a sentence
too. A practice sentence is the same shape -- `ortho` its text, `strokes` all its
words' strokes in order -- plus one `Segment` per word, so the view can say
which word the next stroke belongs to (see `sentenceDecoder`). A single
word has no segments.

`strokes` is the outline the hint shows. `alternates` lists other outlines
that are equally accepted (an affix lesson's long outline next to the short
one, see `util/export_affix_lessons.py`); usually empty. `ruleRanks` names the
expression abbreviation rules the outline uses (ranks in
`expression-lessons.json`, see `util/export_expression_lessons.py`); empty for
every other item. -}
type alias PracticeWord =
    { ortho : String
    , before : String
    , after : String
    , label : String
    , phonology : String
    , steno : String
    , strokes : List (List Int)
    , segments : List Segment
    , alternates : List Outline
    , ruleRanks : List Int
    }


{-| An accepted way of writing an item: its steno text (what the hint and the
typed-strokes line show) and its chords. -}
type alias Outline =
    { steno : String
    , strokes : List (List Int)
    }


{-| One word of a practice sentence: its text as written there, the reading
it has in context, its chord, and how many of the sentence's strokes it takes
(see `util/export_practice_sentences.py`). -}
type alias Segment =
    { text : String
    , label : String
    , steno : String
    , strokeCount : Int
    , spaceBefore : Bool
    }


wordDecoder : D.Decoder PracticeWord
wordDecoder =
    D.succeed PracticeWord
        |> required "ortho" D.string
        |> required "before" D.string
        |> required "after" D.string
        |> required "label" D.string
        |> required "phonology" D.string
        |> required "steno" D.string
        |> required "strokes" (D.list (D.list D.int))
        |> optional "segments" (D.list segmentDecoder) []
        |> optional "alternates" (D.list outlineDecoder) []
        |> optional "ruleRanks" (D.list D.int) []


outlineDecoder : D.Decoder Outline
outlineDecoder =
    D.map2 Outline
        (D.field "steno" D.string)
        (D.field "strokes" (D.list (D.list D.int)))


decoder : D.Decoder (List PracticeWord)
decoder =
    D.list wordDecoder


segmentDecoder : D.Decoder Segment
segmentDecoder =
    D.map5 Segment
        (D.field "text" D.string)
        (D.field "label" D.string)
        (D.field "steno" D.string)
        (D.field "strokeCount" D.int)
        (D.oneOf [ D.field "spaceBefore" D.bool, D.succeed True ])


sentenceDecoder : D.Decoder (List PracticeWord)
sentenceDecoder =
    D.list
        (D.succeed PracticeWord
            |> required "text" D.string
            |> hardcoded ""
            |> hardcoded ""
            |> hardcoded ""
            |> required "phonology" D.string
            |> required "steno" D.string
            |> required "strokes" (D.list (D.list D.int))
            |> required "words" (D.list segmentDecoder)
            |> optional "alternates" (D.list outlineDecoder) []
            |> optional "ruleRanks" (D.list D.int) []
        )


type alias State =
    { words : Array PracticeWord
    , currentWordIndex : Int
    , currentStrokeIndex : Int
    , typed : List (List Int) -- the strokes accepted so far for the current item, in order
    , feedback : Maybe Bool
    }


init : List PracticeWord -> State
init words =
    { words = Array.fromList words
    , currentWordIndex = 0
    , currentStrokeIndex = 0
    , typed = []
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
        , typed = []
    }


{-| Jump `n` words ahead (negative: back) in the current pass, wrapping, and
restart that word at its first stroke. For the "Previous word"/"Next word"
buttons; going past the pass's end just wraps, the pass is reshuffled by
`applyStroke` only. -}
skipWords : Int -> State -> State
skipWords n state =
    { state
        | currentWordIndex = wrappedIndex state (state.currentWordIndex + n)
        , currentStrokeIndex = 0
        , typed = []
        , feedback = Nothing
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


{-| The item's accepted outlines (the primary one first) that start with the
given strokes. -}
consistentOutlines : List (List Int) -> PracticeWord -> List Outline
consistentOutlines typedNow word =
    { steno = word.steno, strokes = word.strokes }
        :: word.alternates
        |> List.filter (\outline -> List.take (List.length typedNow) outline.strokes == typedNow)


{-| The outline the next stroke would continue, were it accepted: the first
(the primary one wins) outline consistent with the strokes so far plus
`observed`. `Main.elm` uses it, on the state BEFORE `applyStroke`, to show
what the learner typed. -}
matchedOutline : Set Int -> State -> Maybe Outline
matchedOutline observed state =
    currentWord state
        |> Maybe.andThen (\word -> consistentOutlines (state.typed ++ [ Set.toList observed ]) word |> List.head)


{-| Advance the drill on a decoded stroke: match -> flash correct, move to the
next stroke (or the next word, wrapping, if that was the word's last stroke);
no match -> flash incorrect, retry the same word/stroke. No counter, no
penalty, no lockout -- deliberately bare minimum.

A stroke matches when the strokes accepted so far plus this one are the start
of ANY accepted outline of the word (`strokes` or one of `alternates`); the
word is done when they are a whole outline. Without alternates this is the
plain one-outline comparison. The hint (`expectedStroke`) stays on `strokes`.

Returns whether this stroke completed the last word of the current pass (the
index wrapped back to 0), so `Main.elm` knows to generate a new shuffle --
this module has no `Cmd`/`Random` access of its own, so it only reports the
boundary rather than acting on it.
-}
applyStroke : Set Int -> State -> ( State, Bool )
applyStroke observed state =
    case currentWord state of
        Just word ->
            let
                typedNow =
                    state.typed ++ [ Set.toList observed ]

                n =
                    List.length typedNow

                consistent =
                    consistentOutlines typedNow word
                        |> List.map .strokes
            in
            if List.isEmpty consistent then
                ( { state | feedback = Just False }, False )

            else if List.any (\outline -> List.length outline == n) consistent then
                let
                    newIndex =
                        wrappedIndex state (state.currentWordIndex + 1)
                in
                ( { state
                    | currentWordIndex = newIndex
                    , currentStrokeIndex = 0
                    , typed = []
                    , feedback = Just True
                  }
                , newIndex == 0
                )

            else
                ( { state
                    | currentStrokeIndex = n
                    , typed = typedNow
                    , feedback = Just True
                  }
                , False
                )

        Nothing ->
            ( state, False )


{-| How the text a learner typed into the Plover capture box stands against the
current item. -}
type TextStatus
    = TextDone -- the whole item's text
    | TextPartial -- the start of it (Plover may still be mid-item, or has just untranslated)
    | TextWrong


{-| Whitespace as Plover emits it: runs collapsed to one space (no-break and narrow
no-break spaces included), the trailing space Plover adds after a word dropped. -}
normalizeText : String -> String
normalizeText text =
    text
        |> String.map
            (\c ->
                if c == '\u{00A0}' || c == '\u{202F}' || c == '\n' || c == '\t' then
                    ' '

                else
                    c
            )
        |> String.words
        |> String.join " "


{-| The same text up to the case of its first character (Plover capitalizes after a
sentence end, and the item's own case is not what the capture box checks). -}
sameText : String -> String -> Bool
sameText expected typed =
    expected == typed || (String.toLower (String.left 1 expected) == String.toLower (String.left 1 typed) && String.dropLeft 1 expected == String.dropLeft 1 typed)


textStatus : String -> PracticeWord -> TextStatus
textStatus typed word =
    let
        expected =
            normalizeText word.ortho

        written =
            normalizeText typed
    in
    if sameText expected written && (not (String.isEmpty written)) then
        TextDone

    else if String.isEmpty written then
        TextPartial

    else if sameText (String.left (String.length written) expected) written then
        TextPartial

    else
        TextWrong


{-| Advance the drill on a text the capture box accepted as the whole item: the
counterpart of the last-stroke branch of `applyStroke` (same pass-boundary flag). -}
applyText : String -> State -> ( State, Bool )
applyText typed state =
    case currentWord state of
        Just word ->
            case textStatus typed word of
                TextDone ->
                    let
                        newIndex =
                            wrappedIndex state (state.currentWordIndex + 1)
                    in
                    ( { state
                        | currentWordIndex = newIndex
                        , currentStrokeIndex = 0
                        , typed = []
                        , feedback = Just True
                      }
                    , newIndex == 0
                    )

                TextPartial ->
                    ( state, False )

                TextWrong ->
                    ( { state | feedback = Just False }, False )

        Nothing ->
            ( state, False )
