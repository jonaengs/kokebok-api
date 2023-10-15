example_input_pannekaker_med_fyll = """\
Pannekaker med fyll
Pannekaker kan fylles med stuing og
spises varme. Fylte pannekaker kan
gjøres ferdig i god tid, drysses med
ost og varmes i stekeovn eller steke-
panne før de skal serveres.
10-12 små pannekaker
stuing:
3 ss hvetemel
3 dl melk
1 ss margarin
2-3 dl fryste grønnsaker (f.eks. er-
ter, gulrøtter)
200 g kokt kjøtt (f.eks. skinke, kjøtt-
pålegg, stek)
eller
200 g kokt fisk, fiskepudding, reker,
krabbe
salt, pepper, muskatnøtt
Lag stuing: Rør ut mel og kald melk
i en liten kjele. Tilsett margarin. Kok
opp under omrøring. La sausen små-
koke i 5 minutter. Tilsett grønnsaker
og oppskåret kjøtt eller fisk. Smak
til med salt og krydder.
Stek tynne pannekaker. Legg 2-3 ss
stuing på hver pannekake og rull
sammen. Stable pannekakene i ste-
kepanna, dryss på litt ost, legg på
lokk og la dem bli gjennomvarme.
Eller legg pannekakene i ildfast
form, dryss på ost og gratiner dem i
ovn ved 200°C i 10 minutter.
"""

example_input_sardinomelett = """\
Sardinomelett
1 eske sardiner
2-3 kokte poteter
½ hakket løk
litt salt og pepper
3 egg
3 ss melk
Stek skivede poteter og løk ved svak
varme i panne. Fordel sardinene
over potetene. Dryss på litt salt og
pepper. Slå over sammenvispet egg
og melk. La det stivne over moderat
varme. Stikk litt i omeletten med en
gaffel slik at den stivner jevnt. Server
den med brød til.
"""

example_output_sardinomelett = """
{
  "title": "Sardinomelett",
  "ingredients": {
    "": [
      "1 eske sardiner",
      "2-3 kokte poteter",
      "½ hakket løk",
      "litt salt og pepper",
      "3 egg",
      "3 ss melk"
    ]
  },
  "instructions": [
    "Stek skivede poteter og løk ved svak varme i panne.",
    "Fordel sardinene over potetene.",
    "Dryss på litt salt og pepper.",
    "Slå over sammenvispet egg og melk.",
    "La det stivne over moderat varme.",
    "Stikk litt i omeletten med en gaffel slik at den stivner jevnt.",
    "Server den med brød til."
  ]
}
"""
