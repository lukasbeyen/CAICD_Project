# Design log: the memory of the sizing harness (version 3: the LLM tutors the RL)

Written by the agents through the `log_entry` tool.

## Session mcp_20261106_135328_611167

### 1. tutor (simulations so far: 101)
Circuit: stage1=diff pair mn1/mp1 (gm1, gain1); stage2=mp3/mn5 (gm6, gain2); Miller Cc+Rc compensates. Cc fights SR vs PM; Rc places LHP zero. Nominal: mn4=18,mn5=18,mp3=20,mn1=24,cap=2p,res=1500,L=90nm all; I_tail=60µA,I2=60µA,SR=30V/µs. Space: mn1[14-24],mn4[13-23],mn5[13-23],mp3[15-24],cap[1p-3p],res[700-1700]. Warm-up(16)+RL(80)+refine(4)=101 sims. RL best: mn4=23,mn1=23,mn5=21,mp3=22,cap=1.5p; SR=31.2✓,gain=652✓,noise=22mV✓,UGBW=29.6MHz✗,PM=35.4°✗. Refine best (cap=1p,mn4=23,mn5=23,mp3=24,res=1700): UGBW+29.5%,SR+25.3% vs RL best. UGBW/PM remain hard gaps; topology likely needs larger mn1 range or longer L.

### 2. reviewer (simulations so far: 101)
Best (reward=-0.681, 101 sims): mn4=23,mn1=23,mn5=23,mp3=24,cap=1pF,res=1700. vs nominal(mn4=18,mn5=18,mp3=20,cap=2p,res=1500): +28%mn4,+28%mn5,+20%mp3,-50%cap,+13%res. Specs: gain=653✓(+227%),SR=39.2✓(+31%),noise=22.5mV✓(-25%),current=185µA✓(-7.5%),area=486pm²✓(-76%),UGBW=38.3MHz✗(-62% vs 100MHz),PM=34.7°✗(-42% vs 60°). Margins: gain+227%,SR+31%,noise-25%,current-7.5%,area-76%; UGBW -62%⚑,PM -42%⚑. Why RL works: mn4↑ raises I_tail→SR↑,UGBW↑(10%/step); mn5/mp3↑ boosts gm6→PM↑(5-6%/step); cap↓ raises UGBW,SR(7%/step); res↑ boosts PM(8%/step). Pareto(area vs current): all top-5 fail specs; none qualify. 0 designs meet all specs. Cost: tutor=101sims(16warm-up+80RL+4refine+1nominal). Fundamental gap: 100MHz UGBW needs search space beyond current bounds.
