"    Red         LightRed        DarkRed
"    Green       LightGreen      DarkGreen       SeaGreen
"    Blue        LightBlue       DarkBlue        SlateBlue
"    Cyan        LightCyan       DarkCyan
"    Magenta     LightMagenta    DarkMagenta
"    Yellow      LightYellow     Brown           DarkYellow
"    Gray        LightGray       DarkGray
"    Black       White
"    Orange      Purple          Violet

if &background == 'dark'
  highlight alloutLevel0 cterm=bold gui=bold ctermfg=Yellow guifg=Yellow
  highlight alloutLevel1 cterm=bold gui=bold ctermfg=LightBlue guifg=LightBlue
  highlight alloutLevel2 cterm=bold gui=bold ctermfg=DarkGreen guifg=Orange
  highlight alloutLevel3 cterm=bold gui=bold ctermfg=LightCyan guifg=LightCyan
  highlight alloutLevel4 cterm=bold gui=bold ctermfg=LightRed guifg=LightRed
  highlight alloutLevel5 cterm=bold gui=bold ctermfg=LightGray guifg=LightGray
  highlight alloutLevel6 cterm=bold gui=bold ctermfg=LightMagenta guifg=LightMagenta
  highlight alloutLevel7 cterm=bold gui=bold ctermfg=LightGreen guifg=LightGreen
  highlight alloutLevel8 cterm=bold gui=bold ctermfg=DarkCyan guifg=Violet
else
  highlight alloutLevel0 cterm=bold gui=bold ctermfg=DarkYellow guifg=DarkYellow
  highlight alloutLevel1 cterm=bold gui=bold ctermfg=Blue guifg=Blue
  highlight alloutLevel2 cterm=bold gui=bold ctermfg=Brown guifg=Brown
  highlight alloutLevel3 cterm=bold gui=bold ctermfg=DarkCyan guifg=DarkCyan
  highlight alloutLevel4 cterm=bold gui=bold ctermfg=Red guifg=Red
  highlight alloutLevel5 cterm=bold gui=bold ctermfg=DarkGray guifg=DarkGray
  highlight alloutLevel6 cterm=bold gui=bold ctermfg=DarkMagenta guifg=DarkMagenta
  highlight alloutLevel7 cterm=bold gui=bold ctermfg=DarkGreen guifg=DarkGreen
  highlight alloutLevel8 cterm=bold gui=bold ctermfg=DarkBlue guifg=Purple
endif

syntax match alloutLevel0 /^\*.*/
syntax match alloutLevel1 /^\.[-*+#.].*/
syntax match alloutLevel2 /^\. [-*+#:].*/
syntax match alloutLevel3 /^\.  [-*+#,].*/
syntax match alloutLevel4 /^\.   [-*+#;].*/
syntax match alloutLevel5 /^\.    [-*+#.].*/
syntax match alloutLevel6 /^\.     [-*+#:].*/
syntax match alloutLevel7 /^\.      [-*+#,].*/
syntax match alloutLevel8 /^\.       [-*+#;].*/
syntax match alloutLevel1 /^\.        [-*+#.].*/
syntax match alloutLevel2 /^\.         [-*+#:].*/
syntax match alloutLevel3 /^\.          [-*+#,].*/
syntax match alloutLevel4 /^\.           [-*+#;].*/
syntax match alloutLevel5 /^\.            [-*+#.].*/
syntax match alloutLevel6 /^\.             [-*+#:].*/
syntax match alloutLevel7 /^\.              [-*+#,].*/
syntax match alloutLevel8 /^\.               [-*+#;].*/

highlight alloutLink gui=bold
syntax match alloutLink /^\. *@.*/
