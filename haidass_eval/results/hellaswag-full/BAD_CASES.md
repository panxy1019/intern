# Bad Cases: hellaswag-full

- Samples: 10042
- Raw incorrect: 6793 (0.676459)
- Length-normalized incorrect: 6227 (0.620096)
- Normalization fixed: 1879
- Normalization hurt: 1313
- Reconstructed normalized prediction mismatches: 0
- Ordering: most confidently wrong after length normalization

## 1. Row 305

- Gold: `0` Even an ordinary rucksack will generally hold this. Choose a location where lots of people pass by and are likely to stop ie.
- Raw predicted: `2` If you're distributing less than 50, you don't need a stall, you just need a decent bag. If you're distributing less than 50, you don't need a stall, you just need a decent bag.
- Normalized predicted: `2` If you're distributing less than 50, you don't need a stall, you just need a decent bag. If you're distributing less than 50, you don't need a stall, you just need a decent bag.
- Normalized wrong-confidence margin: `0.625395`
- Raw scores: `[-112.5, -104.0, -34.25, -80.0]`
- Token lengths: `[28, 35, 54, 22]`
- Normalization character lengths: `[125, 127, 177, 90]`
- Normalized scores: `[-0.9, -0.818898, -0.193503, -0.888889]`

```text
Finance and Business: How to run a campaign stall. Anticipate and gauge interest. This is the hardest part, but be sure you need a stall. If you're distributing less than either 50 magazines/50 slim newspapers/200 a4 or a5 leaflets, then you don't need a stall, you just need a decent bag. 
```

## 2. Row 3686

- Gold: `2`  Blow dry your hair, then use straighteners to make it straighter! However, if you prefer loose curls (or your hair is naturally curly) use a diffuser with a curling balm. This will ensure that the curls are bouncy and full.
- Raw predicted: `0`  Use a good conditioner made for your hair type, wash your hair well and leave your conditioner in for a few minutes, then wash out. Towel dry your hair, comb through with a wide tooth comb.
- Normalized predicted: `0`  Use a good conditioner made for your hair type, wash your hair well and leave your conditioner in for a few minutes, then wash out. Towel dry your hair, comb through with a wide tooth comb.
- Normalized wrong-confidence margin: `0.517716`
- Raw scores: `[-36.5, -85.5, -159.0, -81.0]`
- Token lengths: `[46, 28, 60, 29]`
- Normalization character lengths: `[190, 120, 224, 114]`
- Normalized scores: `[-0.192105, -0.7125, -0.709821, -0.710526]`

```text
Personal Care and Style: How to look good for a night out. Give yourself lots of time before you have to go.. Use a shampoo and conditioner made for your hair type, wash your hair well and leave your conditioner in for a few minutes, then wash out. Towel dry your hair, comb through with a wide tooth comb. 
```

## 3. Row 7599

- Gold: `3` puts a wood sheet in space and put floor tiles.
- Raw predicted: `1` put the wooden poles on the floor and put the wooden floor with the wood floor.
- Normalized predicted: `1` put the wooden poles on the floor and put the wooden floor with the wood floor.
- Normalized wrong-confidence margin: `0.500447`
- Raw scores: `[-70.5, -39.0, -84.5, -48.75]`
- Token lengths: `[14, 17, 19, 11]`
- Normalization character lengths: `[60, 79, 85, 47]`
- Normalized scores: `[-1.175, -0.493671, -0.994118, -1.037234]`

```text
Laying tile: Man is showing a place without the wooden floor and its putting the wooden pole in the floor measuring the space. The man 
```

## 4. Row 1536

- Gold: `3` returns to go over the concepts again as the video closes.
- Raw predicted: `2` throws the ball back down the court and runs to make the serve.
- Normalized predicted: `2` throws the ball back down the court and runs to make the serve.
- Normalized wrong-confidence margin: `0.483378`
- Raw scores: `[-73.5, -52.75, -32.25, -61.75]`
- Token lengths: `[19, 14, 14, 12]`
- Normalization character lengths: `[68, 53, 63, 58]`
- Normalized scores: `[-1.080882, -0.995283, -0.511905, -1.064655]`

```text
Layup drill in basketball: The player starts from one side of the court and runs up and lays up the basketball in the net. He repeats around the court from every angle. The man 
```

## 5. Row 5486

- Gold: `2` bows for the crowd and blows them a kiss.
- Raw predicted: `1` then lifts it over her head.
- Normalized predicted: `1` then lifts it over her head.
- Normalized wrong-confidence margin: `0.460714`
- Raw scores: `[-33.25, -10.375, -36.5, -55.75]`
- Token lengths: `[11, 8, 13, 14]`
- Normalization character lengths: `[40, 28, 41, 59]`
- Normalized scores: `[-0.83125, -0.370536, -0.890244, -0.944915]`

```text
Clean and jerk: A woman is shown preparing to lift a barbell into the air. She lifts it into the air and above her head. She drops the barbell to the ground. She 
```

## 6. Row 6451

- Gold: `3` passes the ball to number 1.
- Raw predicted: `0` men enter the field and throw the ball.
- Normalized predicted: `0` men enter the field and throw the ball.
- Normalized wrong-confidence margin: `0.457692`
- Raw scores: `[-17.25, -36.0, -46.0, -27.75]`
- Token lengths: `[9, 10, 10, 8]`
- Normalization character lengths: `[39, 40, 37, 28]`
- Normalized scores: `[-0.442308, -0.9, -1.243243, -0.991071]`

```text
Playing lacrosse: We see a man in a field in a uniform and a net on a stick. The team appears and run towards the goal. Two men fight over the ball. 50 
```

## 7. Row 6792

- Gold: `1` see one team up close.
- Raw predicted: `1` see one team up close.
- Normalized predicted: `2` watch as the boaters perform handstands in the river.
- Normalized wrong-confidence margin: `0.457011`
- Raw scores: `[-25.5, -24.375, -34.5, -45.25]`
- Token lengths: `[7, 6, 13, 8]`
- Normalization character lengths: `[23, 22, 53, 37]`
- Normalized scores: `[-1.108696, -1.107955, -0.650943, -1.222973]`

```text
Canoeing: We see team of boaters in a competition in the sea. We see the race start and the boaters take off. They pass a small boat in the water. We 
```

## 8. Row 8851

- Gold: `2` ride two camels as a man holds the reins.
- Raw predicted: `0` are getting on and off each camel.
- Normalized predicted: `0` are getting on and off each camel.
- Normalized wrong-confidence margin: `0.455255`
- Raw scores: `[-14.375, -37.25, -36.0, -49.0]`
- Token lengths: `[9, 8, 12, 17]`
- Normalization character lengths: `[34, 32, 41, 53]`
- Normalized scores: `[-0.422794, -1.164062, -0.878049, -0.924528]`

```text
Camel ride: Two camel are sitting in a field. We see people as the get on and off the camels. Four women 
```

## 9. Row 5955

- Gold: `3` adjusted the chair by twisting the screw and then she pedals again.
- Raw predicted: `2` went down the stairs and again went down the stairs and started to pedal.
- Normalized predicted: `2` went down the stairs and again went down the stairs and started to pedal.
- Normalized wrong-confidence margin: `0.447346`
- Raw scores: `[-97.0, -43.75, -24.375, -56.0]`
- Token lengths: `[25, 13, 16, 15]`
- Normalization character lengths: `[120, 56, 73, 67]`
- Normalized scores: `[-0.808333, -0.78125, -0.333904, -0.835821]`

```text
Spinning: A woman went down from the stairs walked towards the cycling machine then started to pedal. The woman 
```

## 10. Row 1661

- Gold: `3` films on front the finish line while people is arriving.
- Raw predicted: `1` shows her how to reach the finish line.
- Normalized predicted: `1` shows her how to reach the finish line.
- Normalized wrong-confidence margin: `0.438545`
- Raw scores: `[-29.125, -15.75, -77.5, -57.5]`
- Token lengths: `[6, 9, 20, 11]`
- Normalization character lengths: `[24, 39, 92, 56]`
- Normalized scores: `[-1.213542, -0.403846, -0.842391, -1.026786]`

```text
Running a marathon: An old woman talks before run in a marathon where there is a lot of people participate. Then, the woman cross the finish line and people help her. A cameraman 
```

## 11. Row 4738

- Gold: `3` In the united states and canada, the exit code is " 011. " if calling from the us or canada, dial these numbers first.
- Raw predicted: `0` You may have to dial this number several times to reach guatemala. You can also use different numbers in different countries to reach guatemala.
- Normalized predicted: `0` You may have to dial this number several times to reach guatemala. You can also use different numbers in different countries to reach guatemala.
- Normalized wrong-confidence margin: `0.429114`
- Raw scores: `[-54.75, -113.0, -139.0, -95.5]`
- Token lengths: `[32, 37, 52, 33]`
- Normalization character lengths: `[144, 138, 169, 118]`
- Normalized scores: `[-0.380208, -0.818841, -0.822485, -0.809322]`

```text
Education and Communications: How to call guatemala. Dial your country's exit code. Every country has what is called an exit code. It's the number you dial in order to direct a call outside the country. 
```

## 12. Row 4652

- Gold: `3` in a blue shirt claps.
- Raw predicted: `2` collapses on a mat.
- Normalized predicted: `1` rushes up and throws the weight onto the field.
- Normalized wrong-confidence margin: `0.420353`
- Raw scores: `[-37.5, -26.625, -18.75, -22.5]`
- Token lengths: `[10, 11, 5, 8]`
- Normalization character lengths: `[34, 47, 19, 22]`
- Normalized scores: `[-1.102941, -0.566489, -0.986842, -1.022727]`

```text
Clean and jerk: He picks up a large weight and lifts it over his head. He drops the weight onto the ground. A man 
```

## 13. Row 6000

- Gold: `2` walks out of frame.
- Raw predicted: `2` walks out of frame.
- Normalized predicted: `0` on the violin while the woman plays the violin.
- Normalized wrong-confidence margin: `0.417553`
- Raw scores: `[-27.625, -47.25, -23.625, -63.5]`
- Token lengths: `[12, 10, 5, 15]`
- Normalization character lengths: `[47, 47, 19, 58]`
- Normalized scores: `[-0.587766, -1.005319, -1.243421, -1.094828]`

```text
Playing violin: A man is seen speaking to another holding a violin. The man speaking them 
```

## 14. Row 9063

- Gold: `0` are holding up axes.
- Raw predicted: `3` are engaged in a game of cricket.
- Normalized predicted: `3` are engaged in a game of cricket.
- Normalized wrong-confidence margin: `0.413826`
- Raw scores: `[-18.125, -35.0, -42.25, -16.25]`
- Token lengths: `[5, 7, 8, 9]`
- Normalization character lengths: `[20, 32, 31, 33]`
- Normalized scores: `[-0.90625, -1.09375, -1.362903, -0.492424]`

```text
Chopping wood: Two men are standing in a forest. They 
```

## 15. Row 8035

- Gold: `0` sits and knits vigorously.
- Raw predicted: `3` starts to hurt herself with the needle.
- Normalized predicted: `3` starts to hurt herself with the needle.
- Normalized wrong-confidence margin: `0.413462`
- Raw scores: `[-26.25, -58.5, -48.5, -23.25]`
- Token lengths: `[8, 14, 8, 9]`
- Normalization character lengths: `[26, 49, 38, 39]`
- Normalized scores: `[-1.009615, -1.193878, -1.276316, -0.596154]`

```text
Knitting: A woman is sitting on wood deck. The woman has red yawn and a needle in her lap. The woman 
```

## 16. Row 3171

- Gold: `3` then uses the tool on the grass in font of him quickly.
- Raw predicted: `0` then begins playing an instrument with his hands.
- Normalized predicted: `0` then begins playing an instrument with his hands.
- Normalized wrong-confidence margin: `0.409639`
- Raw scores: `[-24.5, -75.5, -56.75, -59.0]`
- Token lengths: `[9, 18, 11, 13]`
- Normalization character lengths: `[49, 83, 57, 55]`
- Normalized scores: `[-0.5, -0.909639, -0.995614, -1.072727]`

```text
Cutting the grass: A man is seen standing in a large field holding onto a tool. The man 
```

## 17. Row 7237

- Gold: `1` juices her lemons on a cutting board, with a knife and bowl.
- Raw predicted: `2` pours it into a pitcher and pours it into the lemonade pitcher.
- Normalized predicted: `2` pours it into a pitcher and pours it into the lemonade pitcher.
- Normalized wrong-confidence margin: `0.409524`
- Raw scores: `[-56.0, -56.0, -33.0, -55.0]`
- Token lengths: `[13, 16, 18, 13]`
- Normalization character lengths: `[54, 60, 63, 56]`
- Normalized scores: `[-1.037037, -0.933333, -0.52381, -0.982143]`

```text
Making a lemonade: A woman on screen talks about lemonade. She 
```

## 18. Row 804

- Gold: `2` walks a mower across very tall growing grass.
- Raw predicted: `3` runs and claps his hands together.
- Normalized predicted: `3` runs and claps his hands together.
- Normalized wrong-confidence margin: `0.408088`
- Raw scores: `[-58.0, -46.75, -52.75, -20.125]`
- Token lengths: `[13, 12, 10, 8]`
- Normalization character lengths: `[58, 44, 45, 34]`
- Normalized scores: `[-1.0, -1.0625, -1.172222, -0.591912]`

```text
Cutting the grass: A man touches his faces and waves. The man 
```

## 19. Row 799

- Gold: `1` stop at the bottom and talk.
- Raw predicted: `0` are skiing down a snowy hill.
- Normalized predicted: `0` are skiing down a snowy hill.
- Normalized wrong-confidence margin: `0.40568`
- Raw scores: `[-8.8125, -24.5, -19.125, -24.125]`
- Token lengths: `[9, 7, 8, 10]`
- Normalization character lengths: `[29, 28, 26, 34]`
- Normalized scores: `[-0.303879, -0.875, -0.735577, -0.709559]`

```text
Skiing: People are standing on a hill of snow. People are snowboarding down a hill of snow. People are skiing down a hill. The skiiers 
```

## 20. Row 8460

- Gold: `3` begin and the wording on the screen say's their names are michelle li & cindy gao, and they are shown fighting from various different angles doing many fencing moves.
- Raw predicted: `2` is shown with a loud crowd.
- Normalized predicted: `0` appears and the two begin fencing back and forth.
- Normalized wrong-confidence margin: `0.397298`
- Raw scores: `[-28.625, -37.75, -26.5, -166.0]`
- Token lengths: `[11, 9, 7, 40]`
- Normalization character lengths: `[49, 38, 27, 166]`
- Normalized scores: `[-0.584184, -0.993421, -0.981481, -1.0]`

```text
Doing fencing: People are indoors and the focus is on various clips of various different people fencing one another. A fencing match between two women 
```

## 21. Row 3432

- Gold: `3`  Talk to your doctor about the situation if your child won't take her medication, and see if there is another pill that your child can switch to.. Request an antibiotic with a more appealing taste.
- Raw predicted: `0` Always check with the doctor before giving antibiotics to ensure you are not over-taking a certain antibiotic. There are different brands of antibiotics that act in a similar fashion, but some of them have to be taken more frequently than others.
- Normalized predicted: `0` Always check with the doctor before giving antibiotics to ensure you are not over-taking a certain antibiotic. There are different brands of antibiotics that act in a similar fashion, but some of them have to be taken more frequently than others.
- Normalized wrong-confidence margin: `0.396672`
- Raw scores: `[-68.5, -152.0, -203.0, -133.0]`
- Token lengths: `[46, 37, 48, 41]`
- Normalization character lengths: `[246, 151, 160, 197]`
- Normalized scores: `[-0.278455, -1.006623, -1.26875, -0.675127]`

```text
Family Life: How to get a toddler to take antibiotics. Ask the doctor for an antibiotic that is taken less frequently. This includes giving medicines that are taken once or twice a day as opposed to four times a day. There are different brands of antibiotics that act in a similar fashion, but some of them have to be taken more frequently than others. 
```

## 22. Row 203

- Gold: `2` is ready to lifting weight in middle of a white stage and people behind jim is clapping.
- Raw predicted: `1` is writing people a paper saying white cram.
- Normalized predicted: `0` is sitting in the middle of stage and pour green mascara on his hands leaving it purple and wash it out with soap and water.
- Normalized wrong-confidence margin: `0.38673`
- Raw scores: `[-84.5, -47.0, -97.0, -81.5]`
- Token lengths: `[27, 10, 20, 17]`
- Normalization character lengths: `[124, 44, 88, 74]`
- Normalized scores: `[-0.681452, -1.068182, -1.102273, -1.101351]`

```text
Clean and jerk: Young man is in the middle of stage and its spreading white cram on his hands and walks making deep beraths. Man 
```

## 23. Row 2080

- Gold: `0` hug next to the swimming pool.
- Raw predicted: `2` put a black blindfold on.
- Normalized predicted: `3` argue a bit about the sport but eventually the man wins.
- Normalized wrong-confidence margin: `0.386409`
- Raw scores: `[-36.75, -64.0, -28.875, -35.25]`
- Token lengths: `[8, 18, 7, 12]`
- Normalization character lengths: `[30, 63, 25, 56]`
- Normalized scores: `[-1.225, -1.015873, -1.155, -0.629464]`

```text
Rock-paper-scissors: A man and a woman are playing rock paper scissors. The man gets on his knee and pulls out a ring. They 
```

## 24. Row 6760

- Gold: `2` removed the tv from the wall and installed a wooden tv set furniture, while the other men and the lady arranged the couch and put the pillows on it.
- Raw predicted: `0` walked in the living room in the backyard.
- Normalized predicted: `0` walked in the living room in the backyard.
- Normalized wrong-confidence margin: `0.38244`
- Raw scores: `[-15.4375, -33.0, -111.0, -38.0]`
- Token lengths: `[11, 9, 36, 12]`
- Normalization character lengths: `[42, 37, 148, 46]`
- Normalized scores: `[-0.36756, -0.891892, -0.75, -0.826087]`

```text
Installing carpet: When the new carpet is properly installed, the men vacuum the carpet while the lady walked in the living room. The men and the old man and the woman 
```

## 25. Row 5125

- Gold: `3` continues to polish and repair the dress shoe.
- Raw predicted: `2` uses a large brush to clean a shoe.
- Normalized predicted: `2` uses a large brush to clean a shoe.
- Normalized wrong-confidence margin: `0.373593`
- Raw scores: `[-26.0, -25.75, -14.5, -37.25]`
- Token lengths: `[9, 8, 9, 10]`
- Normalization character lengths: `[33, 31, 35, 46]`
- Normalized scores: `[-0.787879, -0.830645, -0.414286, -0.809783]`

```text
Polishing shoes: A man is standing in front of a fireplace and talking. He shows how to use a small brush on a shoe. He 
```

## 26. Row 7926

- Gold: `2` gets on his knee and pulls out a ring.
- Raw predicted: `0` throws the scissors on the ground.
- Normalized predicted: `0` throws the scissors on the ground.
- Normalized wrong-confidence margin: `0.371033`
- Raw scores: `[-14.5625, -26.625, -30.375, -29.625]`
- Token lengths: `[8, 9, 11, 7]`
- Normalization character lengths: `[34, 27, 38, 30]`
- Normalized scores: `[-0.428309, -0.986111, -0.799342, -0.9875]`

```text
Rock-paper-scissors: A man and a woman are playing rock paper scissors. The man 
```

## 27. Row 8310

- Gold: `1` holds the white puddle and is talking to the camera giving the web adress to the dog salon white shows how comb and shower the dogs.
- Raw predicted: `3` put the brown hair and turn the camera off.
- Normalized predicted: `2` is getting her mane brushed by the woman in the bottom and combing the white away.
- Normalized wrong-confidence margin: `0.370103`
- Raw scores: `[-161.0, -139.0, -56.0, -46.75]`
- Token lengths: `[36, 31, 20, 10]`
- Normalization character lengths: `[144, 132, 82, 43]`
- Normalized scores: `[-1.118056, -1.05303, -0.682927, -1.087209]`

```text
Grooming dog: Woman is with the black dog giving him a shower and styling his hair. Woman is talking while in the bottom a blonde woman is combing a white puddle. Blonde woman 
```

## 28. Row 7854

- Gold: `1` finish on the bikes again.
- Raw predicted: `0` then display the results of the spin class.
- Normalized predicted: `0` then display the results of the spin class.
- Normalized wrong-confidence margin: `0.370017`
- Raw scores: `[-17.875, -27.75, -25.25, -33.0]`
- Token lengths: `[9, 7, 6, 9]`
- Normalization character lengths: `[43, 26, 31, 42]`
- Normalized scores: `[-0.415698, -1.067308, -0.814516, -0.785714]`

```text
Spinning: The spin class is shown again still in progress. The instructor then does floor exercises again with the class following along. The instructor and the class 
```

## 29. Row 6153

- Gold: `3` see the man talking to the camera.
- Raw predicted: `0` see the person sharpening the knife on a cookie sheet.
- Normalized predicted: `0` see the person sharpening the knife on a cookie sheet.
- Normalized wrong-confidence margin: `0.369417`
- Raw scores: `[-20.75, -25.5, -28.25, -25.625]`
- Token lengths: `[12, 8, 6, 8]`
- Normalization character lengths: `[54, 29, 26, 34]`
- Normalized scores: `[-0.384259, -0.87931, -1.086538, -0.753676]`

```text
Sharpening knives: We see a person sharpen a knife on a sanding disc. The person touches it and turns it off. The person turns it on and then off off. We 
```

## 30. Row 2447

- Gold: `0` dries off the shoe using a towel.
- Raw predicted: `2` shows another container of wet wipes.
- Normalized predicted: `2` shows another container of wet wipes.
- Normalized wrong-confidence margin: `0.368633`
- Raw scores: `[-22.25, -33.75, -10.375, -70.5]`
- Token lengths: `[9, 12, 8, 27]`
- Normalization character lengths: `[33, 52, 37, 105]`
- Normalized scores: `[-0.674242, -0.649038, -0.280405, -0.671429]`

```text
Cleaning shoes: The boy shows a container of wet wipes then opens it to pull one out. The boy wipes down the sole of the tennis shoe using the wet wipe towel. The boy 
```

## 31. Row 9726

- Gold: `3` serve the ball while the black man hit the ball back.
- Raw predicted: `2` is playing racket ball while talking to the camera.
- Normalized predicted: `2` is playing racket ball while talking to the camera.
- Normalized wrong-confidence margin: `0.360907`
- Raw scores: `[-100.0, -73.0, -20.375, -43.25]`
- Token lengths: `[30, 23, 11, 12]`
- Normalization character lengths: `[120, 96, 51, 53]`
- Normalized scores: `[-0.833333, -0.760417, -0.39951, -0.816038]`

```text
Tennis serve with ball bouncing: The man in brown shirt is standing next to a pile of tennis ball while he is talking to the camera. He played tennis ball with another person. The man in purple shirt 
```

## 32. Row 1567

- Gold: `2` runs through a skate park down a city street and up stairs.
- Raw predicted: `3` jumps over a trashcan being pushed by a toddler.
- Normalized predicted: `3` jumps over a trashcan being pushed by a toddler.
- Normalized wrong-confidence margin: `0.359012`
- Raw scores: `[-29.5, -68.5, -47.5, -21.0]`
- Token lengths: `[9, 22, 14, 14]`
- Normalization character lengths: `[25, 86, 59, 48]`
- Normalized scores: `[-1.18, -0.796512, -0.805085, -0.4375]`

```text
Powerbocking: The man jumps over a stroller being pushed by a lady. The man jumps over a truck and over a fence losing the cops. The man 
```

## 33. Row 6848

- Gold: `3` is alone doing lay ups to the basket.
- Raw predicted: `1` is moving a dart back and forth on the court.
- Normalized predicted: `1` is moving a dart back and forth on the court.
- Normalized wrong-confidence margin: `0.354444`
- Raw scores: `[-81.5, -29.5, -50.5, -41.5]`
- Token lengths: `[16, 12, 12, 9]`
- Normalization character lengths: `[65, 45, 50, 37]`
- Normalized scores: `[-1.253846, -0.655556, -1.01, -1.121622]`

```text
Layup drill in basketball: Men are playing basket in a roofed wooden court. Man 
```

## 34. Row 1993

- Gold: `0` continues doing it, and the woman has to wipes her mouth and nose several times.
- Raw predicted: `3` pushes another ice cream cone into her mouth.
- Normalized predicted: `3` pushes another ice cream cone into her mouth.
- Normalized wrong-confidence margin: `0.353861`
- Raw scores: `[-59.5, -25.5, -38.25, -13.25]`
- Token lengths: `[18, 9, 15, 10]`
- Normalization character lengths: `[80, 38, 59, 45]`
- Normalized scores: `[-0.74375, -0.671053, -0.648305, -0.294444]`

```text
Having an ice cream: A woman is sitting in a booth. Her little girl shoves a vanilla ice cream cone in her face and laughs. The girl 
```

## 35. Row 4199

- Gold: `1` are represented by blue shirts and white shirts they're wearing.
- Raw predicted: `2` play a game of lacrosse against each other.
- Normalized predicted: `2` play a game of lacrosse against each other.
- Normalized wrong-confidence margin: `0.351108`
- Raw scores: `[-26.25, -42.75, -13.625, -55.75]`
- Token lengths: `[6, 15, 11, 13]`
- Normalization character lengths: `[28, 64, 43, 61]`
- Normalized scores: `[-0.9375, -0.667969, -0.31686, -0.913934]`

```text
Playing lacrosse: There are two teams playing lacrosse in a open field. The teams 
```

## 36. Row 5454

- Gold: `2` in white on the right cheers and the blue team huddle up.
- Raw predicted: `1` missed a shot.
- Normalized predicted: `0` on the left decides to play and wins the game.
- Normalized wrong-confidence margin: `0.350604`
- Raw scores: `[-24.25, -17.875, -59.75, -79.0]`
- Token lengths: `[12, 4, 16, 22]`
- Normalization character lengths: `[46, 14, 57, 90]`
- Normalized scores: `[-0.527174, -1.276786, -1.048246, -0.877778]`

```text
Dodgeball: A referee walks on the floor and tells a player something. A referee walks to a person on the right and tells them they are out. A person 
```

## 37. Row 8503

- Gold: `3` solves it and shows his time.
- Raw predicted: `2` turns it back over.
- Normalized predicted: `2` turns it back over.
- Normalized wrong-confidence margin: `0.347096`
- Raw scores: `[-19.75, -20.75, -7.0, -26.125]`
- Token lengths: `[6, 10, 5, 8]`
- Normalization character lengths: `[27, 29, 19, 29]`
- Normalized scores: `[-0.731481, -0.715517, -0.368421, -0.900862]`

```text
Playing rubik cube: A man is holding a rubiks cube. He then starts to turn it. He stops and looks it over. Eventually he 
```

## 38. Row 5945

- Gold: `3` is behind the man wearinf stilts.
- Raw predicted: `3` is behind the man wearinf stilts.
- Normalized predicted: `0` with a green forest is in front of fruit tree and a man is standing in a fence.
- Normalized wrong-confidence margin: `0.345784`
- Raw scores: `[-60.5, -62.25, -63.75, -44.25]`
- Token lengths: `[19, 17, 14, 10]`
- Normalization character lengths: `[79, 56, 46, 33]`
- Normalized scores: `[-0.765823, -1.111607, -1.38587, -1.340909]`

```text
Powerbocking: Man is jumping wearing stilts on a sidewalk. A calm green grassy field 
```

## 39. Row 671

- Gold: `2`  Keep an eye on the oven so you know when it's fully preheated. Most models with flash an indicator light and/or beep to alert you.
- Raw predicted: `3` You can fill a cake pan with a little bit of cooking spray to help the cake cook faster. Once the cake is ready, remove it from the oven and set it aside.
- Normalized predicted: `3` You can fill a cake pan with a little bit of cooking spray to help the cake cook faster. Once the cake is ready, remove it from the oven and set it aside.
- Normalized wrong-confidence margin: `0.343883`
- Raw scores: `[-69.0, -116.0, -116.0, -52.25]`
- Token lengths: `[30, 45, 35, 36]`
- Normalization character lengths: `[101, 99, 131, 154]`
- Normalized scores: `[-0.683168, -1.171717, -0.885496, -0.339286]`

```text
Food and Entertaining: How to make sour cream coffee cake. Preheat the oven. To ensure that the oven is hot enough to bake the coffee cake, it's important to preheat it. Set the temperature to 350 degrees fahrenheit (177 degrees celsius), and allow it to heat fully. 
```

## 40. Row 6290

- Gold: `3` Once a ball of hair forms, move onto another section of the hair to continue making dreadlocks throughout the hair. The brushing method works best for coarse hair that's 3/4 " to 2.5 " (1.905 cm-6.35 cm) long.
- Raw predicted: `1` Be sure that you brush each small circle evenly; the circular motion of the brush can create tangles. Repeat this process on the other side of your head.
- Normalized predicted: `1` Be sure that you brush each small circle evenly; the circular motion of the brush can create tangles. Repeat this process on the other side of your head.
- Normalized wrong-confidence margin: `0.342288`
- Raw scores: `[-79.0, -68.5, -93.5, -181.0]`
- Token lengths: `[27, 32, 27, 62]`
- Normalization character lengths: `[100, 153, 114, 209]`
- Normalized scores: `[-0.79, -0.447712, -0.820175, -0.866029]`

```text
Personal Care and Style: How to start dreads with short hair. Make small circular motions with a soft bristled brush. Brush small, inch sized circles in a clockwise motion until the hair starts to form into balls. This should only take about a minute or two. 
```

## 41. Row 9976

- Gold: `3` squeeze out the mop in a bucket.
- Raw predicted: `1` is mopping the room in a kitchen.
- Normalized predicted: `1` is mopping the room in a kitchen.
- Normalized wrong-confidence margin: `0.337121`
- Raw scores: `[-32.25, -13.625, -42.25, -31.125]`
- Token lengths: `[10, 9, 9, 10]`
- Normalization character lengths: `[43, 33, 41, 32]`
- Normalized scores: `[-0.75, -0.412879, -1.030488, -0.972656]`

```text
Mooping floor: Man is mopping the floor in a laundry room. Man 
```

## 42. Row 7179

- Gold: `1` spins in a circle with a disc.
- Raw predicted: `1` spins in a circle with a disc.
- Normalized predicted: `0` is attempting to jump with his hands on the ground.
- Normalized wrong-confidence margin: `0.33652`
- Raw scores: `[-25.125, -24.875, -51.25, -44.0]`
- Token lengths: `[11, 9, 13, 12]`
- Normalization character lengths: `[51, 30, 54, 49]`
- Normalized scores: `[-0.492647, -0.829167, -0.949074, -0.897959]`

```text
Shot put: A male athlete is standing on a circle on a track. He 
```

## 43. Row 48

- Gold: `0` starts with some instant coffee and add some water to it which he then adds to some cream.
- Raw predicted: `3` then begins talking about the ingredients needed to make the beverage.
- Normalized predicted: `3` then begins talking about the ingredients needed to make the beverage.
- Normalized wrong-confidence margin: `0.334722`
- Raw scores: `[-62.75, -54.75, -38.0, -25.375]`
- Token lengths: `[19, 13, 12, 12]`
- Normalization character lengths: `[90, 63, 47, 70]`
- Normalized scores: `[-0.697222, -0.869048, -0.808511, -0.3625]`

```text
Having an ice cream: A man comes onto the screen and introduces a video about how to make coffee ice cream. The opening credits for the video are then shown on the screen. The man 
```

## 44. Row 2060

- Gold: `1`  Choose a matte putty instead of a glossy one. If your hair is notably fine, the putty may weigh it down too much.
- Raw predicted: `0` Wait for the putty to sink into your hair. It can take anywhere from two to three minutes for it to penetrate your hair.
- Normalized predicted: `0` Wait for the putty to sink into your hair. It can take anywhere from two to three minutes for it to penetrate your hair.
- Normalized wrong-confidence margin: `0.333333`
- Raw scores: `[-46.0, -82.5, -134.0, -53.75]`
- Token lengths: `[27, 31, 52, 23]`
- Normalization character lengths: `[120, 114, 186, 75]`
- Normalized scores: `[-0.383333, -0.723684, -0.72043, -0.716667]`

```text
Personal Care and Style: How to style short hair (men ). Apply putty to damp hair. Place a small amount of styling putty in the palm of your hand, then rub your hands together to distribute it. Evenly work the product into your hair from end to root. 
```

## 45. Row 481

- Gold: `1` holds the knife and is sharpnening it with the rock.
- Raw predicted: `2` takes the stone out of the white container and puts it onto the ground.
- Normalized predicted: `2` takes the stone out of the white container and puts it onto the ground.
- Normalized wrong-confidence margin: `0.331992`
- Raw scores: `[-57.5, -55.75, -34.75, -55.5]`
- Token lengths: `[17, 13, 15, 16]`
- Normalization character lengths: `[70, 52, 71, 58]`
- Normalized scores: `[-0.821429, -1.072115, -0.489437, -0.956897]`

```text
Sharpening knives: Man is standing in a kitchen in front of a black counter. The man is taking out a grey stone from the green plastic bowl. The man 
```

## 46. Row 5179

- Gold: `0` pulls a line from the waters beneath the hole.
- Raw predicted: `2` uses a fishing pole to fill it with water.
- Normalized predicted: `2` uses a fishing pole to fill it with water.
- Normalized wrong-confidence margin: `0.329322`
- Raw scores: `[-35.0, -51.25, -18.125, -37.25]`
- Token lengths: `[11, 16, 10, 9]`
- Normalization character lengths: `[46, 57, 42, 35]`
- Normalized scores: `[-0.76087, -0.899123, -0.431548, -1.064286]`

```text
Ice fishing: A man is creating a hole in the ice. He 
```

## 47. Row 5651

- Gold: `1` Bring a jacket along, if you don't need it, then use it as a cushion for hard seats/when on the floor.. Sit near the edge of the row.
- Raw predicted: `3` Consequently you may sweat even more if you have nothing to wear. Layer an all-your-clothes skirt or a cardigan on and some boots.
- Normalized predicted: `0` Wear thermal layers or other suitable clothing, since there is a lot of movement going on there at a school assembly. If you dress in loose, layered pieces, such as a dress or skirt, you are more likely to stay warm than if you were to wear loose clothing.
- Normalized wrong-confidence margin: `0.324913`
- Raw scores: `[-133.0, -126.5, -152.0, -112.0]`
- Token lengths: `[57, 37, 44, 33]`
- Normalization character lengths: `[256, 133, 180, 130]`
- Normalized scores: `[-0.519531, -0.951128, -0.844444, -0.861538]`

```text
Home and Garden: How to be comfortable and entertained at a school assembly. Dress in layers. With so many people packed together, the temperature may rise rapidly. Other schools may crank up the air conditioner too much and keep you chilled. 
```

## 48. Row 6295

- Gold: `0` gives the girl something to gargle.
- Raw predicted: `2` puts a third ring in the girl's lip.
- Normalized predicted: `2` puts a third ring in the girl's lip.
- Normalized wrong-confidence margin: `0.323495`
- Raw scores: `[-21.625, -15.0625, -8.4375, -33.75]`
- Token lengths: `[9, 7, 11, 15]`
- Normalization character lengths: `[35, 27, 36, 55]`
- Normalized scores: `[-0.617857, -0.55787, -0.234375, -0.613636]`

```text
Getting a piercing: 3 the guy puts a second ring in the girl's lip. 4 the guy cleans up the girls lip. 5 the guy 
```

## 49. Row 9161

- Gold: `0` have glasses and spoons.
- Raw predicted: `0` have glasses and spoons.
- Normalized predicted: `2` start swinging at each other in a game of tennis.
- Normalized wrong-confidence margin: `0.322279`
- Raw scores: `[-22.0, -35.0, -29.125, -35.25]`
- Token lengths: `[6, 10, 13, 8]`
- Normalization character lengths: `[24, 38, 49, 26]`
- Normalized scores: `[-0.916667, -0.921053, -0.594388, -1.355769]`

```text
Having an ice cream: A girl stands up from a table in a kitchen. She and another girl 
```

## 50. Row 160

- Gold: `3` see a paw's claw up close.
- Raw predicted: `3` see a paw's claw up close.
- Normalized predicted: `0` take the cat to the vet office to be looked at.
- Normalized wrong-confidence margin: `0.321679`
- Raw scores: `[-29.875, -39.25, -36.75, -27.125]`
- Token lengths: `[13, 13, 9, 11]`
- Normalization character lengths: `[47, 41, 36, 26]`
- Normalized scores: `[-0.635638, -0.957317, -1.020833, -1.043269]`

```text
Clipping cat claws: The lady shows us nail clippers. The lady clips her cats claws. The lady shows us a clipped claw. We 
```
