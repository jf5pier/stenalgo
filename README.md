# stenalgo
Stenotype keyboard layout generator


## Objective

Using a genetic algorithm, evolve a stenograph keymap layout that minimize complexity of the theory for a given language. 

## Context

Stenograph keyboards present a limited keyset where multiple keys are pressed at the same time, forming a chord that represent
one or more phoneme / syllable in a word. Steno machines were once proprietary and expensive, but cheaper options are now available
through custom keyboards using popular mechanical keyboards parts and software or firmware interpreter.

Visit the [Open Steno Project](openstenoproject.org) for an in depth introduction to the subject.

There is little added benefit to learning a traditional steno layout if better layouts can be generated. Steno keyboards are not
common and it is unlikely that one will need to use a steno keyboard that is not his own. 

This project aims at generating keymaps and theories for any keyboard layout (number and arrangement of key switches) based on some
keyboard constrains (prefered keys) and using a . 

## Introduction

Stenotyping is done on custom (minimal keys) keybards. The user simultaneously presses multiple keys to form syllables or groups of syllables.
The fingers move as little as possible, but each can press multiple keys situated on the same column (and possible on the same row).

Those keypress (or chord) are interpreted by a software layer implementing a Theory. The theory translate the chord or group of chords into
one or multiple words.

The theory must closely match the syllable(s) pressed to the typed word(s), otherwise learning and remebering the corresponding keypress will
be difficult. It must also distinguish between words that have the same pronunciation, but differnent spellings (homonyms). 

The best theory for a lexicon is as easy to learn and use as possible.

## Minimizing complexity

The algorithm will generate multiple keymap and theory pairs for a given keyboard layout, physiognomical constrains and and lexicon. Those
keymap-theory will be scored based on the strain and complexity in the following ways :

### Finger strain 

The average number of keystroke must be minimized :
- Chords containing less keystrokes are preferable
- Words containing less Chords are preferable
- Common words should contain less strokes than rarely used words
- Movement of fingers should be minimized
- Pressing fewer keys per finger is preferable

### Mental strain

The mapping of keys to the sound they represent must be coherent :
- Phonemes must have a maximum of one canonical representation on the keyboard, one portion of a chord (todo: validate)
- Syllables must have the minimum number of chord representation (variations) on the keyboard to distinguish between the different spellings
- Rules (chord variations) to distinguish between spelling of a syllable must be consistent across a maximum of words sharing that syllable

Words that do not respect an established rule are deemed an exception
- The number of exceptions must be minimized
