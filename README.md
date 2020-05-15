# PyPhyEIS

## 1. What is it?
    
- *PyPhyEIS* is the abbreviation of *Python assisted Physic-based Electrochemical Impedance Spectroscopy* analyzer. It was implemented in Python 3 with PyQt framework for a friendlier user interface, integrated Plotly for graph visualization, and least-squares optimization algorithm from SciPy. 

- It is regrettable that Equivalent Circuit Modeling (ECM) tends to be contrasted with physics-based modellings. ECM, however, without direct and clear physical interpretations, even if excellently describing the experimental data, needs not be done, if the fit parameters cannot be directly and clearly interpretable. Conventional application of ECM in separating resistance values based on fitting using Voigt-type models cannot be considered accurater than the graphical estimation, i.e. reading the characteristic points, when ECM is not properly, albeit simplied, physics-based. 

- A *paradigm shift* in ECM is suggested: Separable or additive capacitance effects like Maxwell-type models are more proper physical description of many systems of interest such as electrochemical and electronic half cells (batteries, supercapactors, fuel cells, solar cells etc.), (polycrystalline) ceramics of mixed conduction (ionic, electronic) and dielectrical properties (ferroelectric, paraelectric). Key components are thus (modified) Debye-type circuits connected in parallel, hierarchical laddernetwork, or transmission line models. Widely applied CPEs (constant phase elements) do not allow clearly defined capacitance effects, thus are suggested to be the root of all evil plaguing ECM practices.   

- ECM can represent succinctly and intuitively complex multiple governing equations and thus test or reveal underlying principles rather easily. Although some free and open-source, and commercial softwares are available and custom-made to a certain extent, algorithms are essential, with which any analytical expressions of impedance can be simulated and fitted and R and C circuit parameters can be interrelated or functions of the variables as temperature, potential, etc. Python programming and accompanying development in data science tools allowed experimental scientists like us to implement ECM, as we wish!   

- In conjuncton with a publication in progress, firstly, a physics-based ECM for battery electrodes, originally suggested by Barsoukov et al. and supported by the fitting program MEISP http://impedance0.tripod.com/#3, is systematically presented in the present Python-assisted platform. The Barsoukov battery model is augmented by recently suggested generic diffusive boundary condition. Barsoukov model for the spherical particles are also implemented in ZView :registered: http://www.scribner.com/software/68-general-electrochemistr376-zview-for-windows/ . In the present Python version, first time, overall chemical capacitance for the diffusion and intercalation process in solid state is formulated consistently for different diffusion geometries. 
![Geometry](https://github.com/thuylinhpham/PyPhyEIS/blob/master/tutorials/Geometry.png)
![Barsoukov](https://github.com/thuylinhpham/PyPhyEIS/blob/master/tutorials/Barsoukov.png) 

## 2.	How to use?

- To run the code directly in your computer using Python commands, you will need to install Python 3.x software and some other libraries from Scipy. For people who are not familiar with a programming language like Python, an executable file named “PyPhyEIS.exe” was created in order to help you use this software by running only the executable file without needing any coding skills nor software installations. The executable file was tested on Windows 10, but technically, it can be run on any version of Windows. 

- The executable file is available at:
https://github.com/thuylinhpham/PyPhyEIS/releases/download/v1.0.2/PyPhyEIS-windows-v1.0.2.rar

- More details please find in the *tutorials* repository.

## 3.	Citation
- Please cite this work as: 

```Thuy Linh Pham, Jong-Sook Lee, Python assisted Physic-based Electrochemical Impedance Spectroscopy, (2020).```

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3820355.svg)](https://doi.org/10.5281/zenodo.3820355)


**Authors**: Thuy Linh Pham (thuylinhbkhn@gmail.com), Jong-Sook Lee (jongsook@jnu.ac.kr)


## 4.	Acknowledgements

- We thank for collaboration with Dr. Namsoo Shin (Deep Solutions Inc, Korea) and Prof. Su-Mi Hur (Chonnam Nat. Univ.)  in Python programming and machine learning tools, Solomon Ansah and Prof. Hoon-Hwe Cho (Hanbat National Univ., Korea) in COMSOL simulations of battery impedance, and Prof. Jaekook Kim in testing real batteries. EIS measurements of batteries and application of Barsoukov model using MEISP were performed by Dr. Eui-Chol Shin, currently at Samsung SDI, during his graduate course at Chonnam National University until 2015. Funding is acknowledged from the National Research Foundation (NRF) of Korea funded by the Ministry of Science and ICT (MSIT) (NRF-2018R1A5A1025224) for Engineering Research Center (ERC) for *Artificial Intelligence Assisted Ionics Based Materials Development Platform* at Chonnam National University, Gwangju, South Korea.

