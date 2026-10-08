module Style exposing (NumberStyle(..), Style(..), label, numberLabel, toggle, toggleNumber)

{-| Which set of punctuation and command chords the trainer teaches and shows: the
Plover English / Lapwing derived one (the default) or the Pluvier / TAO derived one
(see `docs/PLOVER_COMPLEMENTS.md`). Global to the page, like `Notation`, and
session-only: a reload goes back to Plover. The data of both styles comes from
`punctuation-lessons.json`.
-}


type Style
    = Plover
    | Pluvier


toggle : Style -> Style
toggle style =
    case style of
        Plover ->
            Pluvier

        Pluvier ->
            Plover


label : Style -> String
label style =
    case style of
        Plover ->
            "Plover"

        Pluvier ->
            "Pluvier"


{-| Which number theory the trainer teaches and shows: Lapwing's numpad or Pluvier's
number bar (Plover English's bar is Pluvier's, so there are two). A button of its own,
apart from the punctuation `Style`; session-only, the default is Pluvier. The data of
both comes from `number-lessons.json`.
-}
type NumberStyle
    = Lapwing
    | PluvierNumbers


toggleNumber : NumberStyle -> NumberStyle
toggleNumber style =
    case style of
        Lapwing ->
            PluvierNumbers

        PluvierNumbers ->
            Lapwing


numberLabel : NumberStyle -> String
numberLabel style =
    case style of
        Lapwing ->
            "Lapwing"

        PluvierNumbers ->
            "Pluvier"
