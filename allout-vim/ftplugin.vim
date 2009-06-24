" Traitement des fichiers Allout.
" Copyright (C) Progiciels Bourbeau-Pinard, inc.
" François Pinard, 2003-12.

if exists('loaded_allout')
  finish
endif
let loaded_allout = 1

setlocal foldmethod=expr
setlocal foldexpr=AlloutFoldExpr(v:lnum)
setlocal foldtext=AlloutFoldText()
setlocal shiftwidth=1

function AlloutFoldExpr(line)
  let text = getline(a:line)
  if text =~ '^[*.]'
    if text[0] == '*'
      return 1
    endif
    let text2 = substitute(text, '^\.\( *\)[-*+@#.:,;].*', '\1', '')
    if text != text2
      return  strlen(text2) + 2
    endif
  endif
  return &foldnestmax
endfunction

function AlloutFoldText()
  return v:folddashes . ' ' . (v:foldend-v:foldstart) . ' lines '
endfunction

if !has('python')
  finish
endif

let s:save_cpo = &cpo
set cpo&vim

python <<EOF
try:
    import allout
except ImportError:
    import Allout.vim as allout
EOF

" Navigation.

if !hasmapto('<Plug>Allout_next_visible_heading')
  map <buffer> <unique> <LocalLeader>j <Plug>Allout_next_visible_heading
endif
noremap <buffer> <unique> <script> <Plug>Allout_next_visible_heading <SID>next_visible_heading
noremap <silent> <buffer> <SID>next_visible_heading :python allout.next_visible_heading()<CR>

if !hasmapto('<Plug>Allout_previous_visible_heading')
  map <buffer> <unique> <LocalLeader>k <Plug>Allout_previous_visible_heading
endif
noremap <buffer> <unique> <script> <Plug>Allout_previous_visible_heading <SID>previous_visible_heading
noremap <silent> <buffer> <SID>previous_visible_heading :python allout.previous_visible_heading()<CR>

if !hasmapto('<Plug>Allout_up_current_level')
  map <buffer> <unique> <LocalLeader>u <Plug>Allout_up_current_level
endif
noremap <buffer> <unique> <script> <Plug>Allout_up_current_level <SID>up_current_level
noremap <silent> <buffer> <SID>up_current_level :python allout.up_current_level()<CR>

if !hasmapto('<Plug>Allout_forward_current_level')
  map <buffer> <unique> <LocalLeader>l <Plug>Allout_forward_current_level
endif
noremap <buffer> <unique> <script> <Plug>Allout_forward_current_level <SID>forward_current_level
noremap <silent> <buffer> <SID>forward_current_level :python allout.forward_current_level()<CR>

if !hasmapto('<Plug>Allout_backward_current_level')
  map <buffer> <unique> <LocalLeader>h <Plug>Allout_backward_current_level
endif
noremap <buffer> <unique> <script> <Plug>Allout_backward_current_level <SID>backward_current_level
noremap <silent> <buffer> <SID>backward_current_level :python allout.backward_current_level()<CR>

if !hasmapto('<Plug>Allout_end_of_current_entry')
  map <buffer> <unique> <LocalLeader>$ <Plug>Allout_end_of_current_entry
endif
noremap <buffer> <unique> <script> <Plug>Allout_end_of_current_entry <SID>end_of_current_entry
noremap <silent> <buffer> <SID>end_of_current_entry :python allout.end_of_current_entry()<CR>

if !hasmapto('<Plug>Allout_beginning_of_current_entry')
  map <buffer> <unique> <LocalLeader>^ <Plug>Allout_beginning_of_current_entry
endif
noremap <buffer> <unique> <script> <Plug>Allout_beginning_of_current_entry <SID>beginning_of_current_entry
noremap <silent> <buffer> <SID>beginning_of_current_entry :python allout.beginning_of_current_entry()<CR>

" Exposure control.

if !hasmapto('<Plug>Allout_hide_current_subtree')
  map <buffer> <unique> <LocalLeader>c <Plug>Allout_hide_current_subtree
endif
noremap <buffer> <unique> <script> <Plug>Allout_hide_current_subtree <SID>hide_current_subtree
noremap <silent> <buffer> <SID>hide_current_subtree :python allout.hide_current_subtree()<CR>

if !hasmapto('<Plug>Allout_show_children')
  map <buffer> <unique> <LocalLeader>i <Plug>Allout_show_children
endif
noremap <buffer> <unique> <script> <Plug>Allout_show_children <SID>show_children
noremap <silent> <buffer> <SID>show_children :python allout.show_children()<CR>

if !hasmapto('<Plug>Allout_show_current_subtree')
  map <buffer> <unique> <LocalLeader>o <Plug>Allout_show_current_subtree
endif
noremap <buffer> <unique> <script> <Plug>Allout_show_current_subtree <SID>show_current_subtree
noremap <silent> <buffer> <SID>show_current_subtree :python allout.show_current_subtree()<CR>

if !hasmapto('<Plug>Allout_show_all')
  map <buffer> <unique> <LocalLeader>O <Plug>Allout_show_all
endif
noremap <buffer> <unique> <script> <Plug>Allout_show_all <SID>show_all
noremap <silent> <buffer> <SID>show_all :python allout.show_all()<CR>

if !hasmapto('<Plug>Allout_show_current_entry')
  map <buffer> <unique> <LocalLeader>0 <Plug>Allout_show_current_entry
endif
noremap <buffer> <unique> <script> <Plug>Allout_show_current_entry <SID>show_current_entry
noremap <silent> <buffer> <SID>show_current_entry :python allout.show_current_entry()<CR>

" Topic header production.

if !hasmapto('<Plug>Allout_open_sibtopic')
  map <buffer> <unique> <LocalLeader>_ <Plug>Allout_open_sibtopic
endif
noremap <buffer> <unique> <script> <Plug>Allout_open_sibtopic <SID>open_sibtopic
noremap <silent> <buffer> <SID>open_sibtopic :python allout.open_sibtopic()<CR>

if !hasmapto('<Plug>Allout_open_subtopic')
  map <buffer> <unique> <LocalLeader>+ <Plug>Allout_open_subtopic
endif
noremap <buffer> <unique> <script> <Plug>Allout_open_subtopic <SID>open_subtopic
noremap <silent> <buffer> <SID>open_subtopic :python allout.open_subtopic()<CR>

if !hasmapto('<Plug>Allout_open_supertopic')
  map <buffer> <unique> <LocalLeader>- <Plug>Allout_open_supertopic
endif
noremap <buffer> <unique> <script> <Plug>Allout_open_supertopic <SID>open_supertopic
noremap <silent> <buffer> <SID>open_supertopic :python allout.open_supertopic()<CR>

" Topic level and prefix adjustment.

if !hasmapto('<Plug>Allout_normalize_margin')
  map <buffer> <unique> <LocalLeader>= <Plug>Allout_normalize_margin
endif
noremap <buffer> <unique> <script> <Plug>Allout_normalize_margin <SID>normalize_margin
noremap <silent> <buffer> <SID>normalize_margin :python allout.normalize_margin()<CR>

if !hasmapto('<Plug>Allout_shift_in')
  map <buffer> <unique> <LocalLeader>> <Plug>Allout_shift_in
endif
noremap <buffer> <unique> <script> <Plug>Allout_shift_in <SID>shift_in
noremap <silent> <buffer> <SID>shift_in :python allout.shift_in()<CR>

if !hasmapto('<Plug>Allout_shift_out')
  map <buffer> <unique> <LocalLeader>< <Plug>Allout_shift_out
endif
noremap <buffer> <unique> <script> <Plug>Allout_shift_out <SID>shift_out
noremap <silent> <buffer> <SID>shift_out :python allout.shift_out()<CR>

if !hasmapto('<Plug>Allout_rebullet_topic')
  map <buffer> <unique> <LocalLeader><CR> <Plug>Allout_rebullet_topic
endif
noremap <buffer> <unique> <script> <Plug>Allout_rebullet_topic <SID>rebullet_topic
noremap <silent> <buffer> <SID>rebullet_topic :python allout.rebullet_topic()<CR>

if !hasmapto('<Plug>Allout_number_siblings')
  map <buffer> <unique> <LocalLeader># <Plug>Allout_number_siblings
endif
noremap <buffer> <unique> <script> <Plug>Allout_number_siblings <SID>number_siblings
noremap <silent> <buffer> <SID>number_siblings :python allout.number_siblings()<CR>

if !hasmapto('<Plug>Allout_revoke_numbering')
  map <buffer> <unique> <LocalLeader>~ <Plug>Allout_revoke_numbering
endif
noremap <buffer> <unique> <script> <Plug>Allout_revoke_numbering <SID>revoke_numbering
noremap <silent> <buffer> <SID>revoke_numbering :python allout.revoke_numbering()<CR>

" Topic oriented killing and yanking.

if !hasmapto('<Plug>Allout_visual_topic')
  map <buffer> <unique> <LocalLeader>v <Plug>Allout_visual_topic
endif
noremap <buffer> <unique> <script> <Plug>Allout_visual_topic <SID>visual_topic
noremap <silent> <buffer> <SID>visual_topic :python allout.visual_topic()<CR>

if !hasmapto('<Plug>Allout_kill_topic')
  map <buffer> <unique> <LocalLeader>D <Plug>Allout_kill_topic
endif
noremap <buffer> <unique> <script> <Plug>Allout_kill_topic <SID>kill_topic
noremap <silent> <buffer> <SID>kill_topic :python allout.kill_topic()<CR>

python allout.register_key_bindings()

let &cpo = s:save_cpo
