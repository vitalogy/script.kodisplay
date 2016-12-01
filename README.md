
# script.kodisplay

## WIP

## Dependencies:
* pygame
* SDL-1.2
* SDL_image
* SDL_ttf
* RPi.GPIO

## Screenshots

some screenshots from a display with 320x240

### both general (no navigation or media playing)

![](http://milaw.biz/files/kodisplay/general1.png)
![](http://milaw.biz/files/kodisplay/general2.png)

### general & music

![](http://milaw.biz/files/kodisplay/general3.png)
![](http://milaw.biz/files/kodisplay/music.png)

### both navigiation

![](http://milaw.biz/files/kodisplay/navigation1.png)
![](http://milaw.biz/files/kodisplay/navigation2.png)

### video & screensaver

![](http://milaw.biz/files/kodisplay/video.png)
![](http://milaw.biz/files/kodisplay/screensaver.png)

### pvrtv

![](http://milaw.biz/files/kodisplay/pvrtv.png)

## Layout

The layout for the screens/modes can be defined in the file .kodi/userdata/TFT.xml.


## internal used lists


### tftmodeslist (created from layout in TFT.xml)

#### background

| 0 | 1 | 2 |
|---|---|---|
| renderBackground | 'visible' | color |

#### text
| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|----|
| renderText | 'visible' or $Condition | text or $Infolabel | scrollmode | fontname | fontsize | color |  x position | center x | y position | center y |

#### image
| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|----|
| renderImage | 'visible' or $Condition | imagepath or $Infolabel | border | bordercolor | x position | center x | y position | center y | resolution x | resolution y |

#### progressbar
| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|----|
| renderProgressbar | 'visible' | dummy | width | height | color of the background | color of the progress | border in pixel | color of the border | x position | center y |


### querylist

#### background
| 0 | 1 | 2 |
|---|---|---|
| 0 or 1 | 'visible' or 'hide' | color |

#### text
| 0 | 1 | 2 |
|---|---|---|
| 0 or 1 | 'visible' or 'hide' | text |

#### image
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | 'visible' or 'hide' | imagepath | 'local', 'url' or 'noimage' |

#### progressbar
| 0 | 1 | 2 |
|---|---|---|
| 0 or 1 | 'visible' or 'hide' | playtime | |


### renderlist (holds the surfaces)

#### background
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | color |

#### text
| 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 0 or 1 | scrolling surface | rect | text | surface |

#### image
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | imagepath |

#### progressbar
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | playtime |
