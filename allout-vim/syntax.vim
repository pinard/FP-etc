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
  highlight alloutLevel0 gui=bold guifg=Yellow
  highlight alloutLevel1 gui=bold guifg=LightBlue
  highlight alloutLevel2 gui=bold guifg=Orange
  highlight alloutLevel3 gui=bold guifg=LightCyan
  highlight alloutLevel4 gui=bold guifg=LightRed
  highlight alloutLevel5 gui=bold guifg=LightGray
  highlight alloutLevel6 gui=bold guifg=LightMagenta
  highlight alloutLevel7 gui=bold guifg=LightGreen
  highlight alloutLevel8 gui=bold guifg=Violet
else
  highlight alloutLevel0 gui=bold guifg=DarkYellow
  highlight alloutLevel1 gui=bold guifg=Blue
  highlight alloutLevel2 gui=bold guifg=Brown
  highlight alloutLevel3 gui=bold guifg=DarkCyan
  highlight alloutLevel4 gui=bold guifg=Red
  highlight alloutLevel5 gui=bold guifg=DarkGray
  highlight alloutLevel6 gui=bold guifg=DarkMagenta
  highlight alloutLevel7 gui=bold guifg=DarkGreen
  highlight alloutLevel8 gui=bold guifg=Purple
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
