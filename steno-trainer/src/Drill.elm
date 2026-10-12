module Drill exposing (TextStatus(..), textStatus, applyText, Outline, PracticeWord, Progress, Segment, State, applyStroke, currentSegmentIndex, currentWord, decoder, skipWords, matchedOutline, expectedStroke, init, nextWord, progress, progressAfter, reshuffle, sentenceDecoder, shortOutlines, wordDecoder)

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
typed-strokes line show), its chords, and its kind (`util/_outlines.py`): "long"
(the hint above the keyboard), "merged" (merged feature keys), "affix" (an affix
abbreviation, `rule` its rank) or "expression". -}
type alias Outline =
    { steno : String
    , strokes : List (List Int)
    , kind : String
    , rule : Maybe Int
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
    , alternates : List Outline
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
    D.map4 Outline
        (D.field "steno" D.string)
        (D.field "strokes" (D.list (D.list D.int)))
        (D.oneOf [ D.field "kind" D.string, D.succeed "long" ])
        (D.oneOf [ D.field "rule" (D.map Just D.int), D.succeed Nothing ])


decoder : D.Decoder (List PracticeWord)
decoder =
    D.list wordDecoder


segmentDecoder : D.Decoder Segment
segmentDecoder =
    D.map6 Segment
        (D.field "text" D.string)
        (D.field "label" D.string)
        (D.field "steno" D.string)
        (D.field "strokeCount" D.int)
        (D.oneOf [ D.field "spaceBefore" D.bool, D.succeed True ])
        (D.oneOf [ D.field "alternates" (D.list outlineDecoder), D.succeed [] ])


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


{-| Where the strokes typed so far stand in the item: the word (`segment`, 0 for
a lone word), the outline of it being followed and how many of its strokes are
in (`within`), whether the item is `complete`, and the outline and index of the
last stroke typed (`last`, with whether it ended a word). -}
type alias Progress =
    { segment : Int
    , outline : Outline
    , within : Int
    , complete : Bool
    , last : Maybe { outline : Outline, index : Int, endsWord : Bool }
    }


{-| Each word's accepted outlines, the hint first: a lone word's own outline and
its alternates; a sentence's words their slice of the hint strokes and their own
alternates (D24: every word may be written with any of its outlines). -}
segmentOutlines : PracticeWord -> List (List Outline)
segmentOutlines word =
    if List.isEmpty word.segments then
        [ { steno = word.steno, strokes = word.strokes, kind = "long", rule = Nothing } :: word.alternates ]

    else
        word.segments
            |> List.foldl
                (\segment ( start, acc ) ->
                    ( start + segment.strokeCount
                    , ({ steno = segment.steno
                       , strokes = word.strokes |> List.drop start |> List.take segment.strokeCount
                       , kind = "long"
                       , rule = Nothing
                       }
                        :: segment.alternates
                      )
                        :: acc
                    )
                )
                ( 0, [] )
            |> Tuple.second
            |> List.reverse


{-| The first parse (hint outlines first, word by word) of `typed` as whole words
then the start of one; Nothing when the strokes are no accepted way to write the
item. A sentence's own alternates (an abbreviated sentence's rivals) are whole
outlines of the item, tried after the word-by-word parse. -}
progress : PracticeWord -> List (List Int) -> Maybe Progress
progress word typed =
    let
        firstJust options =
            case options of
                [] ->
                    Nothing

                option :: rest ->
                    case option () of
                        Just found ->
                            Just found

                        Nothing ->
                            firstJust rest

        parse index segments remaining last =
            case segments of
                [] ->
                    Nothing

                outlines :: rest ->
                    outlines
                        |> List.map
                            (\outline () ->
                                let
                                    k =
                                        List.length outline.strokes

                                    n =
                                        List.length remaining
                                in
                                if n < k && List.take n outline.strokes == remaining then
                                    Just
                                        { segment = index
                                        , outline = outline
                                        , within = n
                                        , complete = False
                                        , last =
                                            if n > 0 then
                                                Just { outline = outline, index = n - 1, endsWord = False }

                                            else
                                                last
                                        }

                                else if List.take k remaining == outline.strokes then
                                    let
                                        ended =
                                            Just { outline = outline, index = k - 1, endsWord = True }
                                    in
                                    if List.isEmpty rest then
                                        if n == k then
                                            Just { segment = index, outline = outline, within = k, complete = True, last = ended }

                                        else
                                            Nothing

                                    else
                                        parse (index + 1) rest (List.drop k remaining) ended

                                else
                                    Nothing
                            )
                        |> firstJust

        wholeItem =
            if List.isEmpty word.segments then
                []

            else
                List.map (\outline () -> parse 0 [ [ outline ] ] typed Nothing) word.alternates
    in
    firstJust ((\() -> parse 0 (segmentOutlines word) typed Nothing) :: wholeItem)


{-| `progress` of the current item after one more stroke (`observed`). -}
progressAfter : Set Int -> State -> Maybe Progress
progressAfter observed state =
    currentWord state |> Maybe.andThen (\word -> progress word (state.typed ++ [ Set.toList observed ]))


{-| The position in the hint strokes that a progress stands for: the start of its
word in the hint plus the strokes in, kept inside the word (a short outline may
be shorter or longer than the hint's). -}
hintIndex : PracticeWord -> Progress -> Int
hintIndex word p =
    let
        counts =
            if List.isEmpty word.segments then
                [ List.length word.strokes ]

            else
                List.map .strokeCount word.segments

        start =
            counts |> List.take p.segment |> List.sum

        count =
            counts |> List.drop p.segment |> List.head |> Maybe.withDefault 1
    in
    if p.complete then
        List.sum counts

    else
        start + min p.within (max 0 (count - 1))


{-| Which of the current sentence's words the next expected stroke belongs to
(0 for a lone word, which has no segments). -}
currentSegmentIndex : State -> Int
currentSegmentIndex state =
    currentWord state
        |> Maybe.andThen (\word -> progress word state.typed)
        |> Maybe.map .segment
        |> Maybe.withDefault 0


{-| The next stroke of the outline being followed (the hint's until the strokes
typed match only a short one, D25). -}
expectedStroke : State -> Maybe (Set Int)
expectedStroke state =
    currentWord state
        |> Maybe.andThen (\word -> progress word state.typed)
        |> Maybe.andThen (\p -> List.drop p.within p.outline.strokes |> List.head)
        |> Maybe.map Set.fromList


{-| The short outlines (merged, abbreviated) of the current word of the item,
for the hint under the keyboard. -}
shortOutlines : State -> List Outline
shortOutlines state =
    case currentWord state of
        Just word ->
            segmentOutlines word
                |> List.drop (currentSegmentIndex state)
                |> List.head
                |> Maybe.withDefault []
                |> List.filter (\outline -> outline.kind /= "long")

        Nothing ->
            []


{-| The outline the next stroke would continue, were it accepted: the outline
of the word the stroke would be in. `Main.elm` uses it, on the state BEFORE
`applyStroke`, to show what the learner typed. -}
matchedOutline : Set Int -> State -> Maybe Outline
matchedOutline observed state =
    progressAfter observed state |> Maybe.andThen .last |> Maybe.map .outline


{-| Advance the drill on a decoded stroke: match -> flash correct, move to the
next stroke (or the next word, wrapping, if that was the item's last stroke);
no match -> flash incorrect, retry the same word/stroke. No counter, no
penalty, no lockout -- deliberately bare minimum.

A stroke matches when the strokes accepted so far plus this one are a way to
write the item: word by word, each word with any of its outlines (`progress`);
the item is done when every word is whole. `currentStrokeIndex` stays in the
hint's strokes (`hintIndex`), `typed` holds the strokes as typed.

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
            in
            case progress word typedNow of
                Nothing ->
                    ( { state | feedback = Just False }, False )

                Just p ->
                    if p.complete then
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
                            | currentStrokeIndex = hintIndex word p
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
