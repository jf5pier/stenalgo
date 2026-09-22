module Notation exposing (Notation(..), label, layout, render, toggle)

{-| Display-only phonetic notation switch. Everything the trainer loads --
key names, chord-board phonemes, drill steno and phonology -- is in the
single-ASCII-character X-SAMPA dialect of Lexique383 (`src/grammar.py`), which
is also what the Plover dictionary is written in, so X-SAMPA stays the
default and the source of truth; `Ipa` only rewrites strings at view time.
Session-only: a reload goes back to X-SAMPA.
-}

import Dict exposing (Dict)
import Keyboard exposing (Layout)


type Notation
    = XSampa
    | Ipa


toggle : Notation -> Notation
toggle notation =
    case notation of
        XSampa ->
            Ipa

        Ipa ->
            XSampa


label : Notation -> String
label notation =
    case notation of
        XSampa ->
            "X-SAMPA"

        Ipa ->
            "IPA"


{-| Lexique383's X-SAMPA -> IPA, per `src/grammar.py`'s commented-out
`nucleusPhonemesIPA`/`consonantPhonemesIPA`, except "°" (Lexique's schwa,
left untranslated there) -> "ə" and "R" -> "ʁ" (French's usual uvular
fricative, rather than the trill "ʀ"). Characters not in the table (the key
separators "-" and "/", the reserved keys "*", "#", "&", "%", the syllable dot,
and the phonemes spelled identically in both) pass through unchanged. -}
ipaByXSampa : Dict Char String
ipaByXSampa =
    Dict.fromList
        [ ( 'E', "ɛ" )
        , ( '@', "ɑ̃" )
        , ( '°', "ə" )
        , ( '§', "ɔ̃" )
        , ( '5', "ɛ̃" )
        , ( 'O', "ɔ" )
        , ( '9', "œ" )
        , ( '8', "ɥ" )
        , ( '2', "ø" )
        , ( '1', "œ̃" )
        , ( 'R', "ʁ" )
        , ( 'Z', "ʒ" )
        , ( 'S', "ʃ" )
        , ( 'N', "ɲ" )
        , ( 'G', "ŋ" )
        ]


render : Notation -> String -> String
render notation xsampa =
    case notation of
        XSampa ->
            xsampa

        Ipa ->
            String.foldr
                (\c acc -> (Dict.get c ipaByXSampa |> Maybe.withDefault (String.fromChar c)) ++ acc)
                ""
                xsampa


{-| The whole layout's phoneme-bearing strings rewritten, so `Keyboard`'s
views need no notion of notation. Only for display: `Keyboard.geminiKeymap`
keys off `geminiPrLabel`, which this leaves alone. -}
layout : Notation -> Layout -> Layout
layout notation original =
    case notation of
        XSampa ->
            original

        Ipa ->
            let
                r =
                    render notation
            in
            { original
                | keys = List.map (\key -> { key | name = r key.name, phonemes = r key.phonemes }) original.keys
                , phonemeLayers =
                    List.map
                        (\layer ->
                            { layer
                                | phonemesByKey = Dict.map (\_ phonemes -> r phonemes) layer.phonemesByKey
                                , strokes = List.map (\stroke -> { stroke | phonemes = r stroke.phonemes }) layer.strokes
                            }
                        )
                        original.phonemeLayers
                , conjugationMarkers =
                    List.map (\marker -> { marker | keyNames = List.map r marker.keyNames }) original.conjugationMarkers
            }
