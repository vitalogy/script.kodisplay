
# script.kodisplay

## Dependencies:
* pygame
* SDL-1.2
* SDL_image
* SDL_ttf

## Screenshots

some screenshots from a display with 320x240

### both general (no navigation or media playing)

![](http://milaw.biz/files/kodisplay/general1.png)
![](http://milaw.biz/files/kodisplay/general2.png)

### general & music playing

![](http://milaw.biz/files/kodisplay/general3.png)
![](http://milaw.biz/files/kodisplay/music.png)

### both navigiation

![](http://milaw.biz/files/kodisplay/navigation1.png)
![](http://milaw.biz/files/kodisplay/navigation2.png)

### video playing & screensaver

![](http://milaw.biz/files/kodisplay/video.png)
![](http://milaw.biz/files/kodisplay/screensaver.png)

### pvrtv

![](http://milaw.biz/files/kodisplay/pvrtv.png)

## Layout

The layout for the screens/modes can be defined in the file layout.xml in the addon profile directory.
LibreELEC: /storage/.kodi/userdata/addon_data/script.kodisplay/layout.xml


## internal used lists


### layoutlist (created from self defined layout in layout.xml)

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

0 - data was not queried
1 - data was queried

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
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | 'visible' or 'hide' | playtime | duration |


### renderlist (holds the surfaces)

0 - no surface available
1 - surface is available

#### background
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | color |

#### text
| 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 0 or 1 | scrolling surface if needed | rect | text | surface |

#### image
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | imagepath |

#### progressbar
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| 0 or 1 | surface | rect | playtime |


### scrollist (holds text scroll information)

#### text only
| 0 | 1 |
|---|---|
| scroll direction | scroll position |
