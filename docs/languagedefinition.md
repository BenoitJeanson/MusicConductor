# Language definition
A song is structured as followed:
## First line
Ordered information seperated with `;`
  1. ***title***
  2. ***original key*** (e.g. `F`, `Bb`, `F#`)
  3. ***time*** (e.g. `4/4`)
  4. ***tempo*** (e.g. 150)
  5. (optional, default value = 4) the ***bar resolution*** : ie the number of part a bar is divided in.
  
  example:
  ```
  MusicConductor Example; F; 4/4; 150
  ```

## Section
Starts with the character `_` followed by (separated with *line breaks*)
1. separated with commas `;`
  * ***section title*** between `" "`
  * (optional, default = 1) `*` number of ***repetitions*** for the section

example:

```
_"Instru";*2
```

2. ***Barlines*** made of (in any order):
  * ***Bars*** separated with `|` containing 
    * ***Music items*** (see below) separated with space
  * (optional, default = 1) `*` number of ***repetions*** for the line
  * (optional) ***comment*** between `" "`
    
example:

```
"STRINGS" ; Bb|3C7 1Gb7|F|% ; *3
```

## Music item
A Music item is composed of:
* (optional, default value = *bar resolution* (see above)) ***duration*** expressed in one digit [1-9]. When no duration is expressed, this means the music item will cover the whole bar. If not, it's its spanning portion out of the *bar resolution* of the song. The sum of each duration of a bar shall be equal to *bar resolution*
*  a music element that can be:
    * any string (not including separators such as `|`, `;`, `"`, `[`, or ` `)
    * a ***chord*** following the pattern `Key`, `KeyChordtype` or `KeyChordtype\BassKey`
    * optionnally followed by a ***Riff*** which is a list of notes between `[ ]` separated by ` `

Note that a key may be changed from one key map to another (e.g. `Db` to `C#`) to ensure overall consistency with the declared *original key* of the song.

examples:
```
2STOP
%
F#
2F/G
FM7/A
Bb7b9/D
3Bb[A Bb C D]
```

# Run
## Render
The song is embedded in a string `song_str`
To generate the corresponding `html` file
```
sf = SongFactory()
song = sf.parse(song_str)
with open(h_tml_file_name,"w") as f:
    f.write(song.to_html())
```
Add `style.css` found in `./source/`in the repository of the generated file
## Transpose
Based on the previous example, one can change the key with `song.set_key()`. (The originate key of the song is the one declared in the first line of the document)
```
sf = SongFactory()
song = sf.parse(song_str)
song.set_key('F#')
with open(h_tml_file_name,"w") as f:
    f.write(song.to_html())
```
