# geowell

Hér höfum við forrit sem dregur upp gagnvirkt líkan af mögulegum holuferli, sjá skjáskot hér að neðan:

<img src="./screenshots/Holuferilsforrit.png" alt="example screenshot" />

### Uppsetning

1. Setjið upp hreint umhverfi (e. environment) í því pakkastjórnunarumhverfi (e. package manager) sem notandinn kýs. `conda` er t.a.m. góður kandídat.

2. Keyrið eftirfarandi í skipanalínunni:

`> cd [folder]`

`> pip install -r requirements.txt`

`> python setup.py`

### Notkun

Í skipanalínunni:

`> python geowell.py`


### Framtíðarmöguleikar

Þrívíddarmyndin höktir (eðlilega) því gagnvirknin í `matplotlib` var ekki hönnuð með hraða í huga. Hægt væri að exporta holuferilinn (og öllu öðru á þrívíddarmyndinni) yfir í `.vtk` og velta um í hugbúnaði sem hannaður er sérstaklega fyrir slíkt, t.d. _Paraview_.

Skjálftastaðsetningar

Þekktar sprungur

Setja tvívíddarútgáfu af öllu í vafra með `flask` eða `bokeh` og gera framendann meira í átt að GUI í stað 

Hafa gervihnattarmynd á tvívíðu korti (ekki skuggamyndina)

