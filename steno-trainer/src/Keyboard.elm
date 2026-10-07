module Keyboard exposing (AffixRule, ExpressionRule, KeyInfo, Layout, affixRuleDecoder, decoder, expressionRuleDecoder, geminiKeymap, view, viewAffixLegend, viewChordBoard, viewExpressionLegend, viewLegends, viewStrokeLegend, isConjugationStroke, markerPatterns)

{-| The virtual Starboard: decodes `keyboard-layout.json` (exported by
`util/export_keyboard_layout.py` from the repo's own `Starboard` class) and
renders it as a grid, highlighting the keys a given stroke expects/matches.
Also renders the reference material the export includes alongside the
geometry -- the 2-key chord layer as a second, static keyboard (`viewChordBoard`,
mirroring `Starboard.printLayout`'s own "N-key phonemes layer" boards), and the
sparser 3-/4-key thumb chords plus the same-lemma/conjugation marker keys
(Phase P; see `src/ambiguitychecker.py`) as plain-text legends (`viewLegends`).
-}

import Dict exposing (Dict)
import Html exposing (Html, div, h2, h3, li, span, text, ul)
import Html.Attributes exposing (class, classList, style)
import Json.Decode as D
import Json.Decode.Pipeline exposing (required)
import Set exposing (Set)


type alias KeyInfo =
    { index : Int
    , name : String
    , phonemes : String
    , hand : String
    , finger : String
    , row : Int
    , col : Int
    , part : Maybe String
    , reserved : Bool
    , geminiPrLabel : String
    }


keyInfoDecoder : D.Decoder KeyInfo
keyInfoDecoder =
    D.succeed KeyInfo
        |> required "index" D.int
        |> required "name" D.string
        |> required "phonemes" D.string
        |> required "hand" D.string
        |> required "finger" D.string
        |> required "row" D.int
        |> required "col" D.int
        |> required "part" (D.nullable D.string)
        |> required "reserved" D.bool
        |> required "geminiPrLabel" D.string


type alias PhonemeStroke =
    { keys : List Int
    , phonemes : String
    }


type alias PhonemeLayer =
    { keyCount : Int
    , phonemesByKey : Dict Int String
    , strokes : List PhonemeStroke
    }


{-| One same-lemma/conjugation marker group (Phase P): the physical key(s)
chosen for it, and a French label for the grammatical features it marks (e.g.
"impératif, 1re personne" on key "-k"). Distinct from the `*`/`#` keys, which
mark different *lemmas* that happen to sound alike, not inflected forms of one.
-}
type alias ConjugationMarker =
    { keys : List Int
    , keyNames : List String
    , label : String
    }


{-| One affix abbreviation rule (`affix-lessons.json`, `rules`): the keys that
stand for the affix and a French label ("préfixe « re- »"). Shown by
`viewAffixLegend` when the abbreviation hints are on. -}
type alias AffixRule =
    { rank : Int
    , keys : List Int
    , keyNames : List String
    , label : String
    }


affixRuleDecoder : D.Decoder AffixRule
affixRuleDecoder =
    D.map4 AffixRule
        (D.field "rank" D.int)
        (D.field "keys" (D.list D.int))
        (D.field "keyNames" (D.list D.string))
        (D.field "label" D.string)


{-| One expression abbreviation rule (`expression-lessons.json`, `rules`): an
attach rule (its keys add a particle to the neighbouring word) or a brief (one
stroke for a whole phrase, given as `steno`). Shown by `viewExpressionLegend`. -}
type alias ExpressionRule =
    { rank : Int
    , kind : String
    , keys : List Int
    , keyNames : List String
    , steno : Maybe String
    , label : String
    }


expressionRuleDecoder : D.Decoder ExpressionRule
expressionRuleDecoder =
    D.map6 ExpressionRule
        (D.field "rank" D.int)
        (D.field "kind" D.string)
        (D.field "keys" (D.list D.int))
        (D.field "keyNames" (D.list D.string))
        (D.maybe (D.field "steno" D.string))
        (D.field "label" D.string)


type alias Layout =
    { keys : List KeyInfo
    , phonemeLayers : List PhonemeLayer
    , conjugationMarkers : List ConjugationMarker
    }


phonemeStrokeDecoder : D.Decoder PhonemeStroke
phonemeStrokeDecoder =
    D.map2 PhonemeStroke
        (D.field "keys" (D.list D.int))
        (D.field "phonemes" D.string)


phonemeLayerDecoder : D.Decoder PhonemeLayer
phonemeLayerDecoder =
    D.map3 PhonemeLayer
        (D.field "keyCount" D.int)
        (D.field "phonemesByKey" (D.dict D.string) |> D.map intKeyedDict)
        (D.field "strokes" (D.list phonemeStrokeDecoder))


intKeyedDict : Dict String String -> Dict Int String
intKeyedDict =
    Dict.foldl
        (\k v acc ->
            case String.toInt k of
                Just i ->
                    Dict.insert i v acc

                Nothing ->
                    acc
        )
        Dict.empty


conjugationMarkerDecoder : D.Decoder ConjugationMarker
conjugationMarkerDecoder =
    D.map3 ConjugationMarker
        (D.field "keys" (D.list D.int))
        (D.field "keyNames" (D.list D.string))
        (D.field "label" D.string)


decoder : D.Decoder Layout
decoder =
    D.map3 Layout
        (D.field "keys" (D.list keyInfoDecoder))
        (D.field "phonemeLayers" (D.list phonemeLayerDecoder))
        (D.field "conjugationMarkers" (D.list conjugationMarkerDecoder))


{-| Gemini PR label -> Stenalgo key index, built from the same data the
keyboard view renders, so the two can never drift apart.
-}
geminiKeymap : List KeyInfo -> Dict String Int
geminiKeymap keys =
    keys
        |> List.map (\k -> ( k.geminiPrLabel, k.index ))
        |> Dict.fromList


{-| One CSS-grid cell per key: two rows for each side's onset/coda bank, plus
a third row for the thumb clusters and off-home index keys -- close enough to
`Starboard._printableKeyLayout`'s ASCII shape for a first virtual keyboard,
laid out per key by `hand`/`row`/`col` rather than any fixed template.
-}
view : { highlighted : Set Int, correct : Maybe Bool } -> List KeyInfo -> Html msg
view { highlighted, correct } keys =
    div [ class "keyboard" ]
        [ div [ class "hand hand-left" ] (List.filter (\k -> k.hand == "left") keys |> List.map (keyView highlighted correct))
        , div [ class "hand hand-right" ] (List.filter (\k -> k.hand == "right") keys |> List.map (keyView highlighted correct))
        ]


{-| Every phoneme the key writes pressed alone ("wNG", "eO") -- the 1-key
phonemes layer of `Starboard.printLayout`, without `key.name`'s "k-"/"-k"
hand hyphen (the board's left/right halves already say which hand). Keys
with no phoneme of their own (`*`, `#` and the two unassigned reserved keys)
show their name.
-}
keyDisplayName : KeyInfo -> String
keyDisplayName key =
    if String.isEmpty key.phonemes then
        key.name

    else
        key.phonemes


{-| The `*` and `#` star/hash mark keys: drawn like any phoneme key (not dimmed
as reserved) and two rows tall, like the R + wNG pair beside the `*`. -}
isMarkKey : KeyInfo -> Bool
isMarkKey key =
    key.name == "*" || key.name == "#"


keyView : Set Int -> Maybe Bool -> KeyInfo -> Html msg
keyView highlighted correct key =
    let
        isHighlighted =
            Set.member key.index highlighted
    in
    div
        [ classList
            [ ( "key", True )
            , ( "key-reserved", key.reserved && not (isMarkKey key) )
            , ( "key-tall", isMarkKey key )
            , ( "key-expected", isHighlighted )
            , ( "key-correct", isHighlighted && correct == Just True )
            , ( "key-incorrect", isHighlighted && correct == Just False )
            ]
        , style "grid-row"
            (if isMarkKey key then
                String.fromInt (key.row + 1) ++ " / span 2"

             else
                String.fromInt (key.row + 1)
            )
        , style "grid-column" (String.fromInt (key.col + 1))
        ]
        [ text (keyDisplayName key) ]


{-| The second, non-interactive board for the 2-key chord layer: same key
positions as `view`'s, but instead of a label per key, each stroke's phoneme
is drawn once as a small badge straddling the boundary between its two keys
(`Starboard.printLayout`'s "2-key phonemes layer" board). A few pairs on this
layer chord across both hands (the innermost thumb keys), so -- unlike
`view`, whose two hands never need to relate to each other -- this board
places every key in one shared grid, offsetting the right hand's columns
past a spacer column, so a badge can be centered between a pair regardless of
which hand(s) it touches. Badges are positioned by pixel math (`chordKeyCenterX`/
`chordKeyCenterY`, mirroring the `.chord-board` grid's own `rem` geometry in
`style.css`) rather than by spanning the two keys' grid cells: a key can
belong to several pairs, so grid-cell-sized overlays for each pair would
overlap and stack on top of each other.
-}
viewChordBoard : Set Int -> Set Int -> (Set Int -> List Int -> Bool) -> Layout -> Html msg
viewChordBoard lit hint pairAllowed layout =
    case List.filter (\l -> l.keyCount == 2) layout.phonemeLayers of
        layer :: _ ->
            div [ class "phoneme-layer" ] [ viewChordGrid lit hint pairAllowed layout.keys layer.strokes ]

        [] ->
            text ""


{-| Column count of one hand's key grid (`col` ranges 0..5) plus the one
spacer column separating the two hands in the unified chord-board grid.
-}
chordHandColumns : Int
chordHandColumns =
    7


chordKeyColumn : KeyInfo -> Int
chordKeyColumn key =
    key.col + 1 + (if key.hand == "right" then chordHandColumns else 0)


{-| `rem` pitch from one key's left/top edge to the next key's, matching
`.chord-board`'s `grid-auto-rows: 3rem` / column tracks and its `gap: 4px`
(0.25rem at the default 16px root font size).
-}
chordKeyStride : Float
chordKeyStride =
    3.25


chordKeyHalf : Float
chordKeyHalf =
    1.5


{-| Horizontal offset (in `rem`, from the left edge) of the right hand's
column 0: `6 * chordKeyStride` reaches the left edge of the 1.5rem spacer
column (past the 6 left-hand columns, each already including its trailing
gap), then the spacer's own width and one more 0.25rem gap reach the right
hand's first column -- matching `.chord-board`'s `grid-template-columns` of
`repeat(6, 3rem) 1.5rem repeat(6, 3rem)` with a uniform 4px (0.25rem) gap.
-}
chordRightHandOffset : Float
chordRightHandOffset =
    6 * chordKeyStride + 1.5 + 0.25


chordKeyCenterX : KeyInfo -> Float
chordKeyCenterX key =
    let
        base =
            toFloat key.col * chordKeyStride + chordKeyHalf
    in
    if key.hand == "right" then
        base + chordRightHandOffset

    else
        base


chordKeyCenterY : KeyInfo -> Float
chordKeyCenterY key =
    toFloat key.row * chordKeyStride + chordKeyHalf


viewChordGrid : Set Int -> Set Int -> (Set Int -> List Int -> Bool) -> List KeyInfo -> List PhonemeStroke -> Html msg
viewChordGrid lit hint pairAllowed keys strokes =
    let
        -- A badge lights up when both keys of its pair are in the lit stroke
        -- (the Simulate button's current stroke).
        isLit a b =
            glowOf lit a b

        glowOf keySet a b =
            if Set.member a.index keySet && Set.member b.index keySet && pairAllowed keySet [ a.index, b.index ] then
                True

            else
                False

        glow a b =
            if glowOf lit a b then
                LitGlow

            else if glowOf hint a b then
                HintGlow

            else
                NoGlow

        pairs =
            List.filterMap (chordStrokePair keys) strokes

        ( skipPairs, adjacentPairs ) =
            List.partition (\( a, b, _ ) -> chordPairDistance a b > chordAdjacencyThreshold) pairs

        -- A skip pair that shares its outermost key with an adjacent pair
        -- (e.g. [11,13] shares key 11 with adjacent pair [11,12]) is
        -- anchored directly under that adjacent pair's badge, on the same
        -- drop row as any other anchored pair. A skip pair with no such
        -- unambiguous anchor (e.g. [11,14], which shares an outer key with
        -- *two* different adjacent pairs) is centered and dropped to a
        -- second, deeper row instead, so it never lands on the same line as
        -- an anchored badge.
        adjacency =
            chordAdjacency pairs

        ( anchored, unanchored ) =
            List.foldr
                (\pair ( anchoredAcc, unanchoredAcc ) ->
                    let
                        ( a, b, _ ) =
                            pair
                    in
                    case chordAnchorX keys adjacency adjacentPairs a b of
                        Just ( x, kind ) ->
                            ( ( pair, x, kind ) :: anchoredAcc, unanchoredAcc )

                        Nothing ->
                            ( anchoredAcc, pair :: unanchoredAcc )
                )
                ( [], [] )
                skipPairs

        droppedSkipPairs =
            anchored
                ++ (unanchored
                        |> List.sortBy (\( a, b, _ ) -> Tuple.first (chordMidpoint a b))
                        |> chordSpreadBadgeX
                        |> List.map (\( pair, x ) -> ( pair, x, Unanchored ))
                   )
    in
    div [ class "keyboard keyboard-reference chord-board" ]
        (List.map chordKeyView keys
            ++ List.concatMap chordConnectorViews droppedSkipPairs
            ++ chordOverlaysView
                (List.map (\( a, b, label ) -> ( chordMidpoint a b, ( label, glow a b ) )) adjacentPairs
                    ++ List.map (\( ( a, b, label ), badgeX, kind ) -> ( ( badgeX, chordDropYFor kind a b ), ( label, glow a b ) )) droppedSkipPairs
                )
        )


{-| Which side (if either) a skip pair's badge is anchored to: `LoAnchor`
when its leftmost key is the unambiguous cluster edge (e.g. [11,13], badge
aligned under [11,12] and raised slightly), `HiAnchor` for its rightmost key
(e.g. [12,14], badge aligned under [13,14] and lowered slightly), or
`Unanchored` when neither side is unambiguous (e.g. [11,14], badge centered
on its own deeper row). Each case gets a distinct vertical offset and a
distinct horizontal nudge on its connector lines, so lines and badges from
different skip pairs sharing a key (e.g. [11,13] and [11,14] both touch key
11) never fall exactly on top of each other.
-}
type ChordDropKind
    = LoAnchor
    | HiAnchor
    | Unanchored


{-| Every key reachable from `startIndex` by a chain of 2-key strokes (this
board's connected chord "clusters" -- e.g. the four thumb keys form one,
each hand's main bank keys form another). Used to tell whether one of a skip
pair's keys is a true edge of its own cluster, not just of the one pair it's
being compared against.
-}
chordAdjacency : List ( KeyInfo, KeyInfo, String ) -> Dict Int (List Int)
chordAdjacency allPairs =
    allPairs
        |> List.foldl
            (\( a, b, _ ) dict ->
                dict
                    |> Dict.update a.index (\existing -> Just (b.index :: Maybe.withDefault [] existing))
                    |> Dict.update b.index (\existing -> Just (a.index :: Maybe.withDefault [] existing))
            )
            Dict.empty


chordComponent : Dict Int (List Int) -> List KeyInfo -> Int -> List KeyInfo
chordComponent adjacency allKeys startIndex =
    let
        go visited frontier =
            case frontier of
                [] ->
                    visited

                index :: rest ->
                    if Set.member index visited then
                        go visited rest

                    else
                        go (Set.insert index visited) (Maybe.withDefault [] (Dict.get index adjacency) ++ rest)
    in
    go Set.empty [ startIndex ]
        |> Set.toList
        |> List.filterMap (keyByIndex allKeys)


{-| The leftmost and rightmost key (by x position) of a non-empty list. -}
chordExtremes : List KeyInfo -> Maybe ( KeyInfo, KeyInfo )
chordExtremes keyList =
    case keyList of
        first :: rest ->
            Just
                (List.foldl
                    (\k ( loAcc, hiAcc ) ->
                        ( if chordKeyCenterX k < chordKeyCenterX loAcc then
                            k

                          else
                            loAcc
                        , if chordKeyCenterX k > chordKeyCenterX hiAcc then
                            k

                          else
                            hiAcc
                        )
                    )
                    ( first, first )
                    rest
                )

        [] ->
            Nothing


{-| A skip pair's badge aligns under a related adjacent pair's badge only
when exactly one of the skip pair's two keys is a true edge of its own
cluster (e.g. [11,13]'s leftmost key, 11, is also the leftmost key of the
whole 4-key thumb cluster, so it aligns under adjacent pair [11,12]'s
badge -- but [11,14]'s keys are *both* cluster edges, so neither side is
preferred and it's left unanchored). Once a side is picked, the adjacent
pair anchored to is whichever one has that same key as its own edge.
-}
chordAnchorX : List KeyInfo -> Dict Int (List Int) -> List ( KeyInfo, KeyInfo, String ) -> KeyInfo -> KeyInfo -> Maybe ( Float, ChordDropKind )
chordAnchorX allKeys adjacency adjacentPairs a b =
    let
        ( lo, hi ) =
            chordOrderByX a b

        clusterExtremes =
            chordComponent adjacency allKeys lo.index
                |> chordExtremes

        isClusterEdge key =
            case clusterExtremes of
                Just ( loEdge, hiEdge ) ->
                    key.index == loEdge.index || key.index == hiEdge.index

                Nothing ->
                    False
    in
    case ( isClusterEdge lo, isClusterEdge hi ) of
        ( True, False ) ->
            adjacentPairs
                |> List.filter (\( pa, pb, _ ) -> (Tuple.first (chordOrderByX pa pb)).index == lo.index)
                |> List.head
                |> Maybe.map (\( pa, pb, _ ) -> ( Tuple.first (chordMidpoint pa pb), LoAnchor ))

        ( False, True ) ->
            adjacentPairs
                |> List.filter (\( pa, pb, _ ) -> (Tuple.second (chordOrderByX pa pb)).index == hi.index)
                |> List.head
                |> Maybe.map (\( pa, pb, _ ) -> ( Tuple.first (chordMidpoint pa pb), HiAnchor ))

        _ ->
            Nothing


chordOrderByX : KeyInfo -> KeyInfo -> ( KeyInfo, KeyInfo )
chordOrderByX a b =
    if chordKeyCenterX a <= chordKeyCenterX b then
        ( a, b )

    else
        ( b, a )


{-| Resolve a stroke's two key indices to their `KeyInfo`, alongside the
label to display.
-}
chordStrokePair : List KeyInfo -> PhonemeStroke -> Maybe ( KeyInfo, KeyInfo, String )
chordStrokePair keys stroke =
    case List.filterMap (\index -> keyByIndex keys index) stroke.keys of
        [ a, b ] ->
            Just ( a, b, stroke.phonemes )

        _ ->
            Nothing


chordKeyView : KeyInfo -> Html msg
chordKeyView key =
    div
        [ classList
            [ ( "key", True )
            , ( "key-reserved", key.reserved && not (isMarkKey key) )
            ]
        , style "grid-row" (String.fromInt (key.row + 1))
        , style "grid-column" (String.fromInt (chordKeyColumn key))
        ]
        []


{-| Two keys count as physically neighbouring if the gap between their
centers is about one key's stride -- true for every same-row/same-column
pair, and also for the two innermost thumb keys, which sit right against
each other across the (wider) hand-gap spacer. Pairs father apart than that
(the thumb cluster's diagonals, e.g. [11,14]) skip over another key
entirely, so their badge needs a connecting line to make clear which two
keys it belongs to.
-}
chordAdjacencyThreshold : Float
chordAdjacencyThreshold =
    6.0


chordPairDistance : KeyInfo -> KeyInfo -> Float
chordPairDistance a b =
    let
        dx =
            chordKeyCenterX a - chordKeyCenterX b

        dy =
            chordKeyCenterY a - chordKeyCenterY b
    in
    sqrt (dx * dx + dy * dy)


chordMidpoint : KeyInfo -> KeyInfo -> ( Float, Float )
chordMidpoint a b =
    ( (chordKeyCenterX a + chordKeyCenterX b) / 2
    , (chordKeyCenterY a + chordKeyCenterY b) / 2
    )


{-| How far below a non-adjacent pair's own row its badge sits, computed
from the pair's actual key row(s) rather than a hardcoded row index (both
keys share a row for every skip-over pair in today's data; `max` covers the
hypothetical case of a skip pair spanning two rows too). A `LoAnchor` pair is
raised slightly and a `HiAnchor` pair lowered slightly off the shared
anchored-pair line, so two anchored badges never sit at exactly the same
height either; `Unanchored` sits deeper still. Only ever pushed downward,
since the one board that currently has skip-over pairs (the thumb cluster)
is its bottom row, with open space below it; a future layout with
skip-pairs on a top row would need this to push upward instead.
-}
chordDropYFor : ChordDropKind -> KeyInfo -> KeyInfo -> Float
chordDropYFor kind a b =
    let
        rowBottom key =
            toFloat key.row * chordKeyStride + 2 * chordKeyHalf

        anchoredLine =
            max (rowBottom a) (rowBottom b) + chordDropRowSpacing
    in
    case kind of
        LoAnchor ->
            anchoredLine - chordAnchorRaiseLower

        HiAnchor ->
            anchoredLine + chordAnchorRaiseLower

        Unanchored ->
            anchoredLine + chordDropLevelSpacing


{-| Clearance (in `rem`) below a row's bottom edge before the anchored-pair
drop line sits, room enough for the elbow lines to read clearly. -}
chordDropRowSpacing : Float
chordDropRowSpacing =
    1.4


{-| How far (in `rem`) a `LoAnchor` badge is raised, or a `HiAnchor` badge
lowered, off the shared anchored-pair line. -}
chordAnchorRaiseLower : Float
chordAnchorRaiseLower =
    0.4


{-| Extra clearance (in `rem`) between the anchored-pair drop line and the
deeper, unanchored-pair one. -}
chordDropLevelSpacing : Float
chordDropLevelSpacing =
    1.5


{-| Even left-to-right spacing (in `rem`) between neighbouring dropped
badges, wide enough that badges (1.6rem across) never touch. -}
chordSpreadSpacing : Float
chordSpreadSpacing =
    2.6


{-| Assigns each non-adjacent pair (already sorted left-to-right by its
natural midpoint) an evenly-spaced x position centered on the group's
average natural midpoint, so a cluster of several skip-over pairs spreads
out instead of piling up near their shared natural midpoint.
-}
chordSpreadBadgeX : List ( KeyInfo, KeyInfo, String ) -> List ( ( KeyInfo, KeyInfo, String ), Float )
chordSpreadBadgeX sortedPairs =
    let
        n =
            List.length sortedPairs

        center =
            sortedPairs
                |> List.map (\( a, b, _ ) -> Tuple.first (chordMidpoint a b))
                |> List.sum
                |> (\total -> total / toFloat (max 1 n))
    in
    sortedPairs
        |> List.indexedMap
            (\i pair ->
                ( pair, center + (toFloat i - (toFloat n - 1) / 2) * chordSpreadSpacing )
            )


{-| For a non-adjacent pair, an orthogonal (elbow) line from each of its two
keys down to the shared drop row, then across to the badge -- rather than a
diagonal straight line, which reads poorly when several such lines converge
close together. The whole vertical segment is nudged sideways by an amount
depending on the pair's `ChordDropKind`, so that two different skip pairs
sharing a key (e.g. [11,13] and [11,14] both touch key 11) draw their
verticals at different x positions instead of stacking exactly on top of
each other: a `LoAnchor` pair's lines nudge left, a `HiAnchor` pair's nudge
right, and an `Unanchored` pair's two lines nudge outward (away from each
other) by a larger amount than either anchored nudge.
-}
chordConnectorViews : ( ( KeyInfo, KeyInfo, String ), Float, ChordDropKind ) -> List (Html msg)
chordConnectorViews ( ( a, b, _ ), badgeX, kind ) =
    let
        dropY =
            chordDropYFor kind a b

        ( lo, hi ) =
            chordOrderByX a b

        shiftFor key =
            case kind of
                LoAnchor ->
                    -chordAnchorShift

                HiAnchor ->
                    chordAnchorShift

                Unanchored ->
                    if key.index == lo.index then
                        -chordUnanchoredSpread

                    else
                        chordUnanchoredSpread
    in
    chordElbow a badgeX dropY (shiftFor a) ++ chordElbow b badgeX dropY (shiftFor b)


{-| Horizontal nudge (in `rem`) applied to an anchored pair's vertical
connector lines. -}
chordAnchorShift : Float
chordAnchorShift =
    0.4


{-| Horizontal nudge (in `rem`) applied to each of an unanchored pair's two
vertical connector lines, larger than `chordAnchorShift` so they clear an
anchored pair's line sharing the same key (e.g. [11,14]'s left line clears
[11,13]'s, both touching key 11). -}
chordUnanchoredSpread : Float
chordUnanchoredSpread =
    0.8


chordElbow : KeyInfo -> Float -> Float -> Float -> List (Html msg)
chordElbow key badgeX dropY shift =
    let
        x =
            chordKeyCenterX key + shift

        y =
            chordKeyCenterY key
    in
    [ chordConnectorSegment ( x, y ) ( x, dropY )
    , chordConnectorSegment ( x, dropY ) ( badgeX, dropY )
    ]


chordConnectorSegment : ( Float, Float ) -> ( Float, Float ) -> Html msg
chordConnectorSegment ( x1, y1 ) ( x2, y2 ) =
    let
        dx =
            x2 - x1

        dy =
            y2 - y1

        length =
            sqrt (dx * dx + dy * dy)

        angleDeg =
            atan2 dy dx * 180 / pi
    in
    div
        [ class "chord-connector"
        , style "left" (String.fromFloat x1 ++ "rem")
        , style "top" (String.fromFloat y1 ++ "rem")
        , style "width" (String.fromFloat length ++ "rem")
        , style "transform" ("rotate(" ++ String.fromFloat angleDeg ++ "deg)")
        ]
        []


{-| How a badge is lit: by the Simulate run (green), by the hint, the stroke the
drill expects (gray), or not. -}
type Glow
    = NoGlow
    | HintGlow
    | LitGlow


{-| One small phoneme badge per already-positioned stroke. Badges are
grouped by their exact position first and spread apart vertically within a
group before rendering, as a defensive fallback in case two ever land on the
same point (adjacent pairs use a plain midpoint, so e.g. a thumb cluster's
two diagonal pairs could coincide there; `chordDropDepth`'s staggering
already keeps today's data collision-free without relying on this).
-}
chordOverlaysView : List ( ( Float, Float ), ( String, Glow ) ) -> List (Html msg)
chordOverlaysView points =
    points
        |> groupByCenter
        |> List.concatMap viewOverlayGroup


groupByCenter : List ( ( Float, Float ), ( String, Glow ) ) -> List ( ( Float, Float ), List ( String, Glow ) )
groupByCenter points =
    points
        |> List.foldl
            (\( point, label ) acc ->
                Dict.update (pointKey point)
                    (\existing ->
                        case existing of
                            Just ( p, labels ) ->
                                Just ( p, labels ++ [ label ] )

                            Nothing ->
                                Just ( point, [ label ] )
                    )
                    acc
            )
            Dict.empty
        |> Dict.values


pointKey : ( Float, Float ) -> String
pointKey ( x, y ) =
    String.fromFloat x ++ "," ++ String.fromFloat y


{-| Vertical spacing (in `rem`) between co-located badges within a group. -}
chordOverlayCollisionSpacing : Float
chordOverlayCollisionSpacing =
    0.65


viewOverlayGroup : ( ( Float, Float ), List ( String, Glow ) ) -> List (Html msg)
viewOverlayGroup ( ( x, y ), labels ) =
    let
        n =
            List.length labels
    in
    labels
        |> List.indexedMap
            (\i ( label, glowing ) ->
                div
                    [ classList [ ( "chord-overlay", True ), ( "chord-overlay-lit", glowing == LitGlow ), ( "chord-overlay-hint", glowing == HintGlow ) ]
                    , style "left" (String.fromFloat x ++ "rem")
                    , style "top" (String.fromFloat (y + (toFloat i - (toFloat n - 1) / 2) * chordOverlayCollisionSpacing) ++ "rem")
                    ]
                    [ text label ]
            )


keyByIndex : List KeyInfo -> Int -> Maybe KeyInfo
keyByIndex keys index =
    keys |> List.filter (\k -> k.index == index) |> List.head


{-| The two plain-text legends too sparse/small to draw as a board: the
3-/4-key thumb-only chords, the same-lemma/conjugation marker keys, and (once loaded) the affix rules.
Meant for a narrow sidebar column next to the page title, not stacked under
the (tall) keyboards.
-}
viewLegends : Set Int -> Bool -> Set Int -> String -> Layout -> Html msg
viewLegends lit markLit markHighlighted readingLabel layout =
    div [ class "legends" ]
        [ viewConjugationLegend (if markLit then lit else Set.empty) markHighlighted readingLabel layout.conjugationMarkers
        ]


{-| The 3-/4-key thumb strokes, drawn under the chord board like the 2-key
pairs: one mini board per stroke, the same four thumb keys on one line (left
thumb pair, a gap, right thumb pair). The pressed keys are dark (the others
faint), an elbow line drops from each pressed key to a round phoneme badge
under the group, as on the chord board. All groups sit on one line.
-}
viewStrokeLegend : Set Int -> Set Int -> (Set Int -> List Int -> Bool) -> Layout -> Html msg
viewStrokeLegend lit hint strokeAllowed layout =
    let
        strokes =
            layout.phonemeLayers
                |> List.filter (\l -> l.keyCount > 2)
                |> List.concatMap .strokes

        thumbKeys =
            strokes
                |> List.concatMap .keys
                |> Set.fromList
                |> Set.toList
                |> List.filterMap (keyByIndex layout.keys)

        leftKeys =
            List.filter (\k -> k.hand == "left") thumbKeys

        rightKeys =
            List.filter (\k -> k.hand /= "left") thumbKeys

        -- Grid position (0-based slot) of each thumb key: left pair, spacer, right pair.
        slotOf key =
            if key.hand == "left" then
                indexOfKey key leftKeys

            else
                List.length leftKeys + 1 + indexOfKey key rightKeys

        keyCenterX key =
            let
                slot =
                    slotOf key
            in
            if key.hand == "left" then
                toFloat slot * chordKeyStride + chordKeyHalf

            else
                toFloat (List.length leftKeys) * chordKeyStride + 1.75 + toFloat (slot - List.length leftKeys - 1) * chordKeyStride + chordKeyHalf

        dropY =
            2 * chordKeyHalf + 1.1

        keyCell stroke key =
            div
                [ classList [ ( "key", True ), ( "stroke-legend-key", True ), ( "stroke-legend-pressed", List.member key.index stroke.keys ) ]
                , style "grid-row" "1"
                , style "grid-column" (String.fromInt (slotOf key + 1))
                ]
                [ text (keyDisplayName key) ]

        group stroke =
            let
                pressed =
                    List.filterMap (keyByIndex layout.keys) stroke.keys

                -- All three badges are centered under the whole group of four keys (the middle of the gap).
                badgeX =
                    case ( List.map keyCenterX thumbKeys |> List.minimum, List.map keyCenterX thumbKeys |> List.maximum ) of
                        ( Just lo, Just hi ) ->
                            (lo + hi) / 2

                        _ ->
                            0

                -- A group lights when its keys are all down and no bigger group's keys are
                -- (the 4-key "1" must not also light "2" and "5"), and its phoneme is the word's.
                containedIn bigger =
                    List.all (\k -> List.member k bigger.keys) stroke.keys && List.length bigger.keys > List.length stroke.keys

                groupGlowOf keySet =
                    List.all (\k -> Set.member k keySet) stroke.keys
                        && strokeAllowed keySet stroke.keys
                        && not (List.any (\other -> containedIn other && List.all (\k -> Set.member k keySet) other.keys) strokes)

                allLit =
                    groupGlowOf lit

                glowing =
                    if allLit then
                        LitGlow

                    else if groupGlowOf hint then
                        HintGlow

                    else
                        NoGlow
            in
            div
                [ classList [ ( "chord-board", True ), ( "stroke-legend-group", True ), ( "legend-lit", allLit ) ] ]
                (List.map (keyCell stroke) thumbKeys
                    ++ List.concatMap
                        (\key ->
                            [ chordConnectorSegment ( keyCenterX key, 2 * chordKeyHalf ) ( keyCenterX key, dropY )
                            , chordConnectorSegment ( keyCenterX key, dropY ) ( badgeX, dropY )
                            ]
                        )
                        pressed
                    ++ chordOverlaysView [ ( ( badgeX, dropY ), ( stroke.phonemes, glowing ) ) ]
                )
    in
    if List.isEmpty strokes then
        text ""

    else
        div [ class "stroke-legend" ] (List.map group strokes)


indexOfKey : KeyInfo -> List KeyInfo -> Int
indexOfKey key keys =
    keys
        |> List.indexedMap Tuple.pair
        |> List.filter (\( _, k ) -> k.index == key.index)
        |> List.head
        |> Maybe.map Tuple.first
        |> Maybe.withDefault 0


keyLabel : List KeyInfo -> Int -> String
keyLabel keys index =
    keys
        |> List.filter (\k -> k.index == index)
        |> List.head
        |> Maybe.map .name
        |> Maybe.withDefault (String.fromInt index)


viewConjugationLegend : Set Int -> Set Int -> String -> List ConjugationMarker -> Html msg
viewConjugationLegend lit highlighted readingLabel markers =
    div [ class "legend-block" ]
        [ h2 [] [ text "Marqueurs de conjugaison" ]
        , ul [ class "legend" ]
            (markers
                |> List.map
                    (\m ->
                        let
                            isHighlighted =
                                not (Set.isEmpty highlighted) && markerIn highlighted m

                            features =
                                String.split ", " m.label
                                    |> List.map
                                        (\feature ->
                                            span [ classList [ ( "legend-feature", isHighlighted && featureMatches readingLabel feature ) ] ] [ text feature ]
                                        )
                                    |> List.intersperse (text ", ")
                        in
                        li [ classList [ ( "legend-mark", not (Set.isEmpty lit) && markerIn lit m ) ] ]
                            (text (String.join "+" m.keyNames ++ " : ") :: features)
                    )
            )
        ]


{-| Whether one feature of a marker's label ("futur", "3e personne", "pluriel",
"féminin"...) is what the word's reading label (e.g. "indicatif futur, 3e sg.")
says. -}
featureMatches : String -> String -> Bool
featureMatches readingLabel feature =
    let
        label =
            String.toLower readingLabel
    in
    if feature == "pluriel" then
        String.contains " pl." label

    else if feature == "féminin" then
        String.contains " f." label

    else if String.endsWith " personne" feature then
        String.contains (String.dropRight 9 feature ++ " ") label

    else
        String.contains feature label


{-| The pieces of a reading label ("nom, pl. \u{00B7} adjectif, pl.") that the
highlighted conjugation marker stands for: for each of the marker's features the
reading label confirms, the text it shows there ("pl.", "3e", "futur"...).
Empty when no marker is highlighted. -}
markerPatterns : Layout -> Set Int -> String -> List String
markerPatterns layout highlighted readingLabel =
    layout.conjugationMarkers
        |> List.filter (\m -> not (Set.isEmpty highlighted) && markerIn highlighted m)
        |> List.concatMap (\m -> String.split ", " m.label)
        |> List.filter (featureMatches readingLabel)
        |> List.map
            (\feature ->
                if feature == "pluriel" then
                    "pl."

                else if feature == "f\u{00E9}minin" then
                    "f."

                else if String.endsWith " personne" feature then
                    String.dropRight 9 feature

                else
                    feature
            )


{-| Whether a marker's keys are all in `stroke` (a stroke made of marker keys alone
can hold several markers: "-st" is the plural and the third person). -}
markerIn : Set Int -> ConjugationMarker -> Bool
markerIn stroke marker =
    List.all (\k -> Set.member k stroke) marker.keys


markerKeys : Layout -> Set Int
markerKeys layout =
    layout.conjugationMarkers |> List.concatMap .keys |> Set.fromList


{-| Whether `stroke` is made of conjugation marker keys alone, one or several: the extra
stroke a conjugated form ends with (the Simulate button lights it yellow). -}
isConjugationStroke : Layout -> List Int -> Bool
isConjugationStroke layout stroke =
    let
        keys =
            Set.fromList stroke
    in
    not (Set.isEmpty keys) && Set.isEmpty (Set.diff keys (markerKeys layout))


{-| The affix rules, one per line: key names, then the affix they stand for.
Shown under the chord board when the "Affix rule hint" toggle is on. -}
viewAffixLegend : List AffixRule -> Html msg
viewAffixLegend rules =
    div [ class "legend-block" ]
        [ h3 [] [ text "Affix rules" ]
        , ul [ class "legend" ]
            (rules
                |> List.map (\r -> li [] [ text (groupKeyNames r.keyNames ++ " : " ++ r.label) ])
            )
        ]


{-| The expression rules the current item uses, one per line: the keys of an
attach rule (key names grouped per side) or the stroke of a brief, then what
they stand for. Shown under the chord board when the abbreviation hint is on. -}
viewExpressionLegend : List ExpressionRule -> Html msg
viewExpressionLegend rules =
    div [ class "legend-block" ]
        [ h3 [] [ text "Expression rules" ]
        , ul [ class "legend" ]
            (rules
                |> List.map
                    (\r ->
                        li []
                            [ text
                                ((case r.steno of
                                    Just steno ->
                                        steno

                                    Nothing ->
                                        groupKeyNames r.keyNames
                                 )
                                    ++ " : "
                                    ++ r.label
                                )
                            ]
                    )
            )
        ]


{-| A rule's key names with the keys of one side grouped: `-j`, `-s`, `-d` ->
`-jsd`; `w-`, `p-`, `-j` -> `wp- + -j`. Left-hand names end with `-`,
right-hand ones start with it (any other name stays as it is, after them). -}
groupKeyNames : List String -> String
groupKeyNames names =
    let
        left =
            List.filter (String.endsWith "-") names

        right =
            List.filter (\n -> String.startsWith "-" n && not (String.endsWith "-" n)) names

        other =
            List.filter (\n -> not (List.member n left || List.member n right)) names

        leftText =
            if List.isEmpty left then
                []

            else
                [ String.concat (List.map (String.dropRight 1) left) ++ "-" ]

        rightText =
            if List.isEmpty right then
                []

            else
                [ "-" ++ String.concat (List.map (String.dropLeft 1) right) ]
    in
    String.join " + " (leftText ++ rightText ++ other)
