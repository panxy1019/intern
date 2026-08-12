# Bad Cases: piqa-full

- Samples: 1838
- Raw incorrect: 605 (0.329162)
- Length-normalized incorrect: 599 (0.325898)
- Normalization fixed: 188
- Normalization hurt: 182
- Reconstructed normalized prediction mismatches: 0
- Ordering: most confidently wrong after length normalization

## 1. Row 927

- Gold: `0`  breask the lock
- Raw predicted: `1`  use a key to open
- Normalized predicted: `1`  use a key to open
- Normalized wrong-confidence margin: `1.222549`
- Raw scores: `[-30.25, -13.5]`
- Token lengths: `[4, 5]`
- Normalization character lengths: `[15, 17]`
- Normalized scores: `[-2.016667, -0.794118]`

```text
Question: how to open a lock illegally?
Answer:
```

## 2. Row 698

- Gold: `0`  Can be cut by sciscors with ease
- Raw predicted: `1`  Can be cut by a knife with ease
- Normalized predicted: `1`  Can be cut by a knife with ease
- Normalized wrong-confidence margin: `0.887349`
- Raw scores: `[-63.75, -34.25]`
- Token lengths: `[9, 8]`
- Normalization character lengths: `[32, 31]`
- Normalized scores: `[-1.992188, -1.104839]`

```text
Question: sleeves
Answer:
```

## 3. Row 636

- Gold: `1`  add slicia packets to the plate.
- Raw predicted: `0`  use a heat gun each day to dry the moisture from the dome.
- Normalized predicted: `0`  use a heat gun each day to dry the moisture from the dome.
- Normalized wrong-confidence margin: `0.75`
- Raw scores: `[-50.75, -52.0]`
- Token lengths: `[15, 8]`
- Normalization character lengths: `[58, 32]`
- Normalized scores: `[-0.875, -1.625]`

```text
Question: how to keep a cake from drying out over several days?
Answer:
```

## 4. Row 421

- Gold: `1`  can wipe saw 
- Raw predicted: `1`  can wipe saw 
- Normalized predicted: `0`  can wipe dish towel 
- Normalized wrong-confidence margin: `0.740385`
- Raw scores: `[-37.5, -34.0]`
- Token lengths: `[6, 5]`
- Normalization character lengths: `[20, 13]`
- Normalized scores: `[-1.875, -2.615385]`

```text
Question: blanket
Answer:
```

## 5. Row 1358

- Gold: `1`  writes on air 
- Raw predicted: `0`  writes on the ground 
- Normalized predicted: `0`  writes on the ground 
- Normalized wrong-confidence margin: `0.717262`
- Raw scores: `[-26.0, -27.375]`
- Token lengths: `[5, 4]`
- Normalization character lengths: `[21, 14]`
- Normalized scores: `[-1.238095, -1.955357]`

```text
Question: sky writer airplane
Answer:
```

## 6. Row 531

- Gold: `1`  Crisco
- Raw predicted: `0`  Frosting
- Normalized predicted: `0`  Frosting
- Normalized wrong-confidence margin: `0.677083`
- Raw scores: `[-8.25, -10.25]`
- Token lengths: `[3, 2]`
- Normalization character lengths: `[8, 6]`
- Normalized scores: `[-1.03125, -1.708333]`

```text
Question: What is the best thing to brush onto your skillet to season it?
Answer:
```

## 7. Row 1623

- Gold: `1`  finish, woodgrain with  bobby pin 
- Raw predicted: `0`  replace drawer with bobby pin 
- Normalized predicted: `0`  replace drawer with bobby pin 
- Normalized wrong-confidence margin: `0.643627`
- Raw scores: `[-40.25, -67.5]`
- Token lengths: `[9, 12]`
- Normalization character lengths: `[30, 34]`
- Normalized scores: `[-1.341667, -1.985294]`

```text
Question: dresser
Answer:
```

## 8. Row 1079

- Gold: `1`  can hear a bird  ride by
- Raw predicted: `1`  can hear a bird  ride by
- Normalized predicted: `0`  can hear record the sound of a birds wings ride by
- Normalized wrong-confidence margin: `0.624583`
- Raw scores: `[-62.0, -44.75]`
- Token lengths: `[11, 7]`
- Normalization character lengths: `[50, 24]`
- Normalized scores: `[-1.24, -1.864583]`

```text
Question: listen
Answer:
```

## 9. Row 1162

- Gold: `0`  Use superglue
- Raw predicted: `1`  Use a soldering iron
- Normalized predicted: `1`  Use a soldering iron
- Normalized wrong-confidence margin: `0.620673`
- Raw scores: `[-15.625, -11.625]`
- Token lengths: `[4, 5]`
- Normalization character lengths: `[13, 20]`
- Normalized scores: `[-1.201923, -0.58125]`

```text
Question: To attach magnets to a piece of wood, you can
Answer:
```

## 10. Row 1382

- Gold: `0`  can act as patch  on a real person's bed
- Raw predicted: `1`  can act as a comforter on a real person's bed
- Normalized predicted: `1`  can act as a comforter on a real person's bed
- Normalized wrong-confidence margin: `0.615278`
- Raw scores: `[-71.5, -52.75]`
- Token lengths: `[12, 14]`
- Normalization character lengths: `[40, 45]`
- Normalized scores: `[-1.7875, -1.172222]`

```text
Question: handkerchief
Answer:
```

## 11. Row 112

- Gold: `1`  you life them with your arms.
- Raw predicted: `0`  you lift them with your ankles.
- Normalized predicted: `0`  you lift them with your ankles.
- Normalized wrong-confidence margin: `0.602336`
- Raw scores: `[-22.75, -38.75]`
- Token lengths: `[9, 7]`
- Normalization character lengths: `[31, 29]`
- Normalized scores: `[-0.733871, -1.336207]`

```text
Question: how do you use dumbbell bars?
Answer:
```

## 12. Row 224

- Gold: `0`  sits floor 
- Raw predicted: `0`  sits floor 
- Normalized predicted: `1`  sits cardboard box 
- Normalized wrong-confidence margin: `0.581938`
- Raw scores: `[-26.375, -34.5]`
- Token lengths: `[4, 5]`
- Normalization character lengths: `[11, 19]`
- Normalized scores: `[-2.397727, -1.815789]`

```text
Question: sofa
Answer:
```

## 13. Row 885

- Gold: `1`  You have to defeat Apollo Creed and Clubber Lang first.
- Raw predicted: `0`  Drago isn't in this game because it was released before Rocky IV.
- Normalized predicted: `0`  Drago isn't in this game because it was released before Rocky IV.
- Normalized wrong-confidence margin: `0.559091`
- Raw scores: `[-42.25, -66.5]`
- Token lengths: `[17, 13]`
- Normalization character lengths: `[65, 55]`
- Normalized scores: `[-0.65, -1.209091]`

```text
Question: To fight Ivan Drago in Rocky for sega master system.
Answer:
```

## 14. Row 440

- Gold: `1`  Use a tide pen to target the stain.
- Raw predicted: `0`  Wipe the stain with a rag and dish soap.
- Normalized predicted: `0`  Wipe the stain with a rag and dish soap.
- Normalized wrong-confidence margin: `0.540625`
- Raw scores: `[-26.375, -42.0]`
- Token lengths: `[12, 9]`
- Normalization character lengths: `[40, 35]`
- Normalized scores: `[-0.659375, -1.2]`

```text
Question: To get a stain out of clothes.
Answer:
```

## 15. Row 686

- Gold: `1`  Offer to let them in on BOGO ticket.
- Raw predicted: `1`  Offer to let them in on BOGO ticket.
- Normalized predicted: `0`  Put the best show you have on free display but in the back of the circus. By time they get to that display they'll have spent a bundle
- Normalized wrong-confidence margin: `0.51109`
- Raw scores: `[-126.0, -52.25]`
- Token lengths: `[32, 11]`
- Normalization character lengths: `[134, 36]`
- Normalized scores: `[-0.940299, -1.451389]`

```text
Question: How to get people to come to the carnival.
Answer:
```

## 16. Row 1421

- Gold: `1`  is stored with a  whisk 
- Raw predicted: `0`  can start fires with a whisk 
- Normalized predicted: `0`  can start fires with a whisk 
- Normalized wrong-confidence margin: `0.50431`
- Raw scores: `[-47.0, -51.0]`
- Token lengths: `[8, 8]`
- Normalization character lengths: `[29, 24]`
- Normalized scores: `[-1.62069, -2.125]`

```text
Question: pitcher
Answer:
```

## 17. Row 491

- Gold: `0`  quench kindle 
- Raw predicted: `0`  quench kindle 
- Normalized predicted: `1`  quench rice cooker 
- Normalized wrong-confidence margin: `0.50094`
- Raw scores: `[-32.25, -34.25]`
- Token lengths: `[5, 6]`
- Normalization character lengths: `[14, 19]`
- Normalized scores: `[-2.303571, -1.802632]`

```text
Question: toilet
Answer:
```

## 18. Row 92

- Gold: `1`  chops cars down.
- Raw predicted: `0`  chops windows down.
- Normalized predicted: `0`  chops windows down.
- Normalized wrong-confidence margin: `0.496711`
- Raw scores: `[-34.5, -37.0]`
- Token lengths: `[5, 5]`
- Normalization character lengths: `[19, 16]`
- Normalized scores: `[-1.815789, -2.3125]`

```text
Question: Jig Saw
Answer:
```

## 19. Row 452

- Gold: `1`  Add small amount of 7UP in vase.
- Raw predicted: `0`  Add small amount of coffee in vase.
- Normalized predicted: `0`  Add small amount of coffee in vase.
- Normalized wrong-confidence margin: `0.49308`
- Raw scores: `[-25.125, -38.75]`
- Token lengths: `[9, 11]`
- Normalization character lengths: `[35, 32]`
- Normalized scores: `[-0.717857, -1.210938]`

```text
Question: Extend life of flowers in vase.
Answer:
```

## 20. Row 276

- Gold: `1`  Keep them in hampers, split if certain colors are washed separately.
- Raw predicted: `0`  Keep them in a pile in the corner of your room so you always have access to them.
- Normalized predicted: `0`  Keep them in a pile in the corner of your room so you always have access to them.
- Normalized wrong-confidence margin: `0.48484`
- Raw scores: `[-38.75, -65.5]`
- Token lengths: `[19, 15]`
- Normalization character lengths: `[81, 68]`
- Normalized scores: `[-0.478395, -0.963235]`

```text
Question: How do you organize dirty clothes?
Answer:
```

## 21. Row 1156

- Gold: `0`  stop fires 
- Raw predicted: `0`  stop fires 
- Normalized predicted: `1`  stop flooding 
- Normalized wrong-confidence margin: `0.482143`
- Raw scores: `[-27.5, -28.25]`
- Token lengths: `[3, 3]`
- Normalization character lengths: `[11, 14]`
- Normalized scores: `[-2.5, -2.017857]`

```text
Question: liquid
Answer:
```

## 22. Row 10

- Gold: `1`  roll in flour and dep fry
- Raw predicted: `0`  pat dry before frying
- Normalized predicted: `0`  pat dry before frying
- Normalized wrong-confidence margin: `0.480238`
- Raw scores: `[-26.875, -44.0]`
- Token lengths: `[5, 6]`
- Normalization character lengths: `[21, 25]`
- Normalized scores: `[-1.279762, -1.76]`

```text
Question: fried pickles
Answer:
```

## 23. Row 619

- Gold: `1`  Skewer the meat and put on grill.
- Raw predicted: `0`  Place the kebab meat on the grill.
- Normalized predicted: `0`  Place the kebab meat on the grill.
- Normalized wrong-confidence margin: `0.472371`
- Raw scores: `[-11.5, -26.75]`
- Token lengths: `[11, 11]`
- Normalization character lengths: `[34, 33]`
- Normalized scores: `[-0.338235, -0.810606]`

```text
Question: To cook the kebab meat on a grill
Answer:
```

## 24. Row 1240

- Gold: `0`  read the codes with a machine.
- Raw predicted: `1`  ask it what's wrong with it.
- Normalized predicted: `1`  ask it what's wrong with it.
- Normalized wrong-confidence margin: `0.460119`
- Raw scores: `[-31.75, -16.75]`
- Token lengths: `[7, 9]`
- Normalization character lengths: `[30, 28]`
- Normalized scores: `[-1.058333, -0.598214]`

```text
Question: how do you find out what's wrong with a car?
Answer:
```

## 25. Row 503

- Gold: `0`  add some other runs and tears to give it a stylish effect.
- Raw predicted: `1`  glue the edges of the run together with fabric glue.
- Normalized predicted: `1`  glue the edges of the run together with fabric glue.
- Normalized wrong-confidence margin: `0.451426`
- Raw scores: `[-65.5, -35.25]`
- Token lengths: `[14, 11]`
- Normalization character lengths: `[58, 52]`
- Normalized scores: `[-1.12931, -0.677885]`

```text
Question: To use tights that have been ruined by a run,
Answer:
```

## 26. Row 1495

- Gold: `1`  Dig Cement 
- Raw predicted: `1`  Dig Cement 
- Normalized predicted: `0`  Dig Underwater 
- Normalized wrong-confidence margin: `0.434091`
- Raw scores: `[-25.875, -23.75]`
- Token lengths: `[4, 4]`
- Normalization character lengths: `[15, 11]`
- Normalized scores: `[-1.725, -2.159091]`

```text
Question: Excavator
Answer:
```

## 27. Row 1741

- Gold: `0`  can cover a shovel .
- Raw predicted: `0`  can cover a shovel .
- Normalized predicted: `1`  is more useful than a shovel .
- Normalized wrong-confidence margin: `0.433333`
- Raw scores: `[-36.5, -41.75]`
- Token lengths: `[6, 8]`
- Normalization character lengths: `[20, 30]`
- Normalized scores: `[-1.825, -1.391667]`

```text
Question: mold
Answer:
```

## 28. Row 1787

- Gold: `1`  can hold together a  diaper 
- Raw predicted: `1`  can hold together a  diaper 
- Normalized predicted: `0`  can hold together a  thick stack of paper 
- Normalized wrong-confidence margin: `0.431548`
- Raw scores: `[-60.25, -52.25]`
- Token lengths: `[10, 8]`
- Normalization character lengths: `[42, 28]`
- Normalized scores: `[-1.434524, -1.866071]`

```text
Question: safety pin
Answer:
```

## 29. Row 86

- Gold: `0`  cry them out
- Raw predicted: `1`  ignore them
- Normalized predicted: `1`  ignore them
- Normalized wrong-confidence margin: `0.428977`
- Raw scores: `[-16.125, -10.0625]`
- Token lengths: `[3, 2]`
- Normalization character lengths: `[12, 11]`
- Normalized scores: `[-1.34375, -0.914773]`

```text
Question: how to let go of feelings?
Answer:
```

## 30. Row 977

- Gold: `1`  empty Tic Tac containers.
- Raw predicted: `0`  an empty milk jug.
- Normalized predicted: `0`  an empty milk jug.
- Normalized wrong-confidence margin: `0.428889`
- Raw scores: `[-20.0, -38.5]`
- Token lengths: `[6, 7]`
- Normalization character lengths: `[18, 25]`
- Normalized scores: `[-1.111111, -1.54]`

```text
Question: To store spices at home using recycled materials, you can use
Answer:
```

## 31. Row 808

- Gold: `1`  can draw on a  face 
- Raw predicted: `1`  can draw on a  face 
- Normalized predicted: `0`  can draw on a  blackboard 
- Normalized wrong-confidence margin: `0.426923`
- Raw scores: `[-43.5, -42.0]`
- Token lengths: `[8, 7]`
- Normalization character lengths: `[26, 20]`
- Normalized scores: `[-1.673077, -2.1]`

```text
Question: marker
Answer:
```

## 32. Row 822

- Gold: `0`  sing to them only
- Raw predicted: `1`  sing to a group of people.
- Normalized predicted: `1`  sing to a group of people.
- Normalized wrong-confidence margin: `0.42336`
- Raw scores: `[-19.375, -18.625]`
- Token lengths: `[4, 7]`
- Normalization character lengths: `[17, 26]`
- Normalized scores: `[-1.139706, -0.716346]`

```text
Question: how do you serenade someone?
Answer:
```

## 33. Row 1555

- Gold: `0`  Rub TechNu on your skin before going out.
- Raw predicted: `1`  Rub Poison Oak on your skin before going out.
- Normalized predicted: `1`  Rub Poison Oak on your skin before going out.
- Normalized wrong-confidence margin: `0.422493`
- Raw scores: `[-56.5, -43.0]`
- Token lengths: `[11, 11]`
- Normalization character lengths: `[41, 45]`
- Normalized scores: `[-1.378049, -0.955556]`

```text
Question: How can you avoid being affected by Poison Ivy?
Answer:
```

## 34. Row 17

- Gold: `0`  Wrap panythose around wire coat hanger bent into a square frame.
- Raw predicted: `1`  Wrap newspaper around wire coat hanger bent into a square frame.
- Normalized predicted: `1`  Wrap newspaper around wire coat hanger bent into a square frame.
- Normalized wrong-confidence margin: `0.421875`
- Raw scores: `[-92.0, -65.0]`
- Token lengths: `[16, 14]`
- Normalization character lengths: `[64, 64]`
- Normalized scores: `[-1.4375, -1.015625]`

```text
Question: Create a filtering net.
Answer:
```

## 35. Row 1517

- Gold: `1`  use a power buffer
- Raw predicted: `1`  use a power buffer
- Normalized predicted: `0`  use a power washer, with liquid wax
- Normalized wrong-confidence margin: `0.420238`
- Raw scores: `[-30.5, -23.25]`
- Token lengths: `[9, 4]`
- Normalization character lengths: `[35, 18]`
- Normalized scores: `[-0.871429, -1.291667]`

```text
Question: what is the best way to apply car wax?
Answer:
```

## 36. Row 225

- Gold: `1`  place on box on top of another.
- Raw predicted: `0`  place one box next to another.
- Normalized predicted: `0`  place one box next to another.
- Normalized wrong-confidence margin: `0.412634`
- Raw scores: `[-17.5, -30.875]`
- Token lengths: `[7, 8]`
- Normalization character lengths: `[30, 31]`
- Normalized scores: `[-0.583333, -0.995968]`

```text
Question: how do you stack boxes?
Answer:
```

## 37. Row 737

- Gold: `1`  can hold cups 
- Raw predicted: `1`  can hold cups 
- Normalized predicted: `0`  can hold pennies. 
- Normalized wrong-confidence margin: `0.404762`
- Raw scores: `[-34.5, -32.5]`
- Token lengths: `[7, 4]`
- Normalization character lengths: `[18, 14]`
- Normalized scores: `[-1.916667, -2.321429]`

```text
Question: Wire Racks
Answer:
```

## 38. Row 791

- Gold: `1`  can be used to write  words
- Raw predicted: `0`  can be used to speak words
- Normalized predicted: `0`  can be used to speak words
- Normalized wrong-confidence margin: `0.398148`
- Raw scores: `[-26.0, -37.75]`
- Token lengths: `[6, 7]`
- Normalization character lengths: `[26, 27]`
- Normalized scores: `[-1.0, -1.398148]`

```text
Question: lipstick
Answer:
```

## 39. Row 919

- Gold: `1`  you look everwhere for it
- Raw predicted: `0`  you look for it in one place
- Normalized predicted: `0`  you look for it in one place
- Normalized wrong-confidence margin: `0.397679`
- Raw scores: `[-21.625, -29.25]`
- Token lengths: `[7, 6]`
- Normalization character lengths: `[28, 25]`
- Normalized scores: `[-0.772321, -1.17]`

```text
Question: how do you scavenge for something?
Answer:
```

## 40. Row 1327

- Gold: `1`  Pay attention to the arrow markers. These indicate which way to insert the filter into the slot.
- Raw predicted: `0`  Air filters can be installed in any direction.
- Normalized predicted: `0`  Air filters can be installed in any direction.
- Normalized wrong-confidence margin: `0.387455`
- Raw scores: `[-12.125, -62.5]`
- Token lengths: `[9, 19]`
- Normalization character lengths: `[46, 96]`
- Normalized scores: `[-0.263587, -0.651042]`

```text
Question: Which direction to properly install an air filter.
Answer:
```

## 41. Row 1050

- Gold: `0`  can be used to milk cow into
- Raw predicted: `0`  can be used to milk cow into
- Normalized predicted: `1`  can be used to insulate against boiling water into
- Normalized wrong-confidence margin: `0.386071`
- Raw scores: `[-34.75, -42.75]`
- Token lengths: `[7, 10]`
- Normalization character lengths: `[28, 50]`
- Normalized scores: `[-1.241071, -0.855]`

```text
Question: stainless steel bucket
Answer:
```

## 42. Row 1570

- Gold: `0`  arrange a simple pet cage around it.
- Raw predicted: `1`  drape a blanket over the devices to hide them.
- Normalized predicted: `1`  drape a blanket over the devices to hide them.
- Normalized wrong-confidence margin: `0.381944`
- Raw scores: `[-45.25, -40.25]`
- Token lengths: `[8, 11]`
- Normalization character lengths: `[36, 46]`
- Normalized scores: `[-1.256944, -0.875]`

```text
Question: To keep your entertainment center safe from children,
Answer:
```

## 43. Row 817

- Gold: `1`  can enlarge drawer when lit
- Raw predicted: `0`  Can be made from drawer alone
- Normalized predicted: `0`  Can be made from drawer alone
- Normalized wrong-confidence margin: `0.376756`
- Raw scores: `[-38.75, -46.25]`
- Token lengths: `[7, 6]`
- Normalization character lengths: `[29, 27]`
- Normalized scores: `[-1.336207, -1.712963]`

```text
Question: microscope
Answer:
```

## 44. Row 1224

- Gold: `1`  can hold pens 
- Raw predicted: `0`  can hold cans 
- Normalized predicted: `0`  can hold cans 
- Normalized wrong-confidence margin: `0.375`
- Raw scores: `[-21.5, -26.75]`
- Token lengths: `[5, 4]`
- Normalization character lengths: `[14, 14]`
- Normalized scores: `[-1.535714, -1.910714]`

```text
Question: cans
Answer:
```

## 45. Row 1764

- Gold: `1`  can be wiped up by napkin 
- Raw predicted: `1`  can be wiped up by napkin 
- Normalized predicted: `0`  can be wiped up by ice cream scoop 
- Normalized wrong-confidence margin: `0.36456`
- Raw scores: `[-49.5, -46.25]`
- Token lengths: `[12, 9]`
- Normalization character lengths: `[35, 26]`
- Normalized scores: `[-1.414286, -1.778846]`

```text
Question: baby powder
Answer:
```

## 46. Row 688

- Gold: `0`  Test the cap and see if it breaks the seal to open.
- Raw predicted: `1`  See if there is any water missing from the bottle.
- Normalized predicted: `1`  See if there is any water missing from the bottle.
- Normalized wrong-confidence margin: `0.340343`
- Raw scores: `[-43.75, -25.875]`
- Token lengths: `[13, 11]`
- Normalization character lengths: `[51, 50]`
- Normalized scores: `[-0.857843, -0.5175]`

```text
Question: How do you tell if a water bottle has been opened?
Answer:
```

## 47. Row 964

- Gold: `0`  can melt humans 
- Raw predicted: `1`  can melt water 
- Normalized predicted: `1`  can melt water 
- Normalized wrong-confidence margin: `0.335417`
- Raw scores: `[-33.5, -26.375]`
- Token lengths: `[4, 4]`
- Normalization character lengths: `[16, 15]`
- Normalized scores: `[-2.09375, -1.758333]`

```text
Question: fire
Answer:
```

## 48. Row 716

- Gold: `0`  wiping  noses cleanly
- Raw predicted: `1`  wiping  hands cleanly
- Normalized predicted: `1`  wiping  hands cleanly
- Normalized wrong-confidence margin: `0.333333`
- Raw scores: `[-49.0, -42.0]`
- Token lengths: `[7, 6]`
- Normalization character lengths: `[21, 21]`
- Normalized scores: `[-2.333333, -2.0]`

```text
Question: tissues
Answer:
```

## 49. Row 868

- Gold: `1`  Use a Quikcrete's Vinyl Concrete Patcher in order to smooth down all the cracks.
- Raw predicted: `0`  Fill the cracks with dirt in order to smooth down all the cracks.
- Normalized predicted: `0`  Fill the cracks with dirt in order to smooth down all the cracks.
- Normalized wrong-confidence margin: `0.317308`
- Raw scores: `[-42.75, -78.0]`
- Token lengths: `[14, 24]`
- Normalization character lengths: `[65, 80]`
- Normalized scores: `[-0.657692, -0.975]`

```text
Question: How do we patch the concrete cracks?
Answer:
```

## 50. Row 1762

- Gold: `0`  can store footballs  
- Raw predicted: `1`  can store bicycles 
- Normalized predicted: `1`  can store bicycles 
- Normalized wrong-confidence margin: `0.31485`
- Raw scores: `[-38.25, -28.625]`
- Token lengths: `[6, 5]`
- Normalization character lengths: `[21, 19]`
- Normalized scores: `[-1.821429, -1.506579]`

```text
Question: baskets
Answer:
```
