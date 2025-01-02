<div align="center">
    <img src="base/static/media/favicon.png" alt="favicon" height="100px">
</div>

<div align="center">
    <h1 style="font-size:4em;">Herd Genetics</h1>
</div>


[Herd Genetics](https://herdgenetics.com), a full stack web simulation, dedicated to
teaching about animal genetics. ***Simulate breeding programs, focusing on PTAs, genetic
recessives and inbreeding coefficients.*** Herd Genetics aims for accuracy of PTA/Trait
correlations and trends. It is a classroom based system targeting group learning with
every simulation belonging to a class.

Available at https://herdgenetics.com

<p align="center">
    <img src="base/static/media/banner5.webp" alt="cow">
</p>

## Compatability

Herd Genetics seeks to replace the original
[Cow Progress](https://github.com/Owen-Dechow/cow_progress/tree/main) application. While
Cow Progress only had support for Holstein Breeding programs, Herd Genetics make it a
goal to diversify the possible animals through front end animal filters. To maintain
compatability legacy traitsets from the original simulation program have been imported
into Herd Genetics. Those traitsets only allow for Bovine (Holstein) filters.


## System Changes

Although backwards compatability is impotent to Herd Genetics, certain systems have been
replaced from the original program.

### 1. Inbreeding Calculator

The original Cow Progress program used an older version of
[python-inbreeding](https://github.com/Owen-Dechow/inbreeding-python) to calculate
inbreeding coefficients. Herd Genetics uses an updated version of that some package which
accounts for inbreeding of common ancestors.

### 2. XLSX Files

Cow Progress allowed users to export data in a `.xlsx` file for analysis in Excel. Herd
Genetics uses `.csv` files over the excel format due to size and speed benefits. CSV
files can be loaded into Excel just as XLSX file would be.

### 3. PTAs

Cow Progress only contained phenotypes and genotypes. Herd Genetics adds to this with
PTAs.

### 4. Bull Phenotypes

In Cow Progress both males (bulls) and females (cows) had phenotypes. In Herd Genetics
male phenotypes are equivilent to their mother's (dam) or `null` if they do not have a
known mother. 

### 5. Multi Animal Support

Cow Progress only allowed for Bovine Holsteins. Herd Genetics allows for "animal filter."
Animal filters change the terminology, traits, and recessives used. This is controlled
by each student.

<p align="center">
    <img src="base/static/media/banner8.webp" alt="dog">
</p>

## License

Herd Genetics is licensed under the MIT License. A copy of license can be found on the
[Github repository](https://github.com/Owen-Dechow/herdgen/blob/main/LICENSE.md) or in the
[local repository](/LICENSE.md). Pease adhere to the terms and conditions of the license.

## Resources

The following are a list of resources helpful to those seeking a better understanding of
what this simulation is meant to accomplish.

* [Net merit as a measure of lifetime profit: 2021 revision](https://www.ars.usda.gov/ARSUserFiles/80420530/Publications/ARR/nmcalc-2021_ARR-NM8.pdf)
* [Genetic Correlations for HOL breed](https://www.ars.usda.gov/arsuserfiles/80420530/publications/arr/nm8%20supplemental%20table_correlations_2021.txt)
* [How To Read Holstein Sire Information](https://www.holsteinusa.com/pdf/print_material/read_sire_%20info.pdf)

<p align="center">
    <img src="base/static/media/banner11.webp" alt="goats">
</p>

## Development Tools, Packages, & References

The following are a list tools, packages, and references used in the creation and
codebase of Herd Genetics.

### Webserver
* [Django](https://www.djangoproject.com/) - Web Framework
* [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/) - Web Framework Tools
* [django-environ](https://django-environ.readthedocs.io/en/latest/) - Environment Variable Management
* [gunicorn](https://gunicorn.org/) - Webserver Management
* [whitenoise](https://github.com/evansd/whitenoise) - Static File Service
* [certifi](https://github.com/certifi/python-certifi) - SSL Certificate Management
* [NGINX](https://nginx.org/en/) - Webserver Management
* [Supervisor](http://supervisord.org/introduction.html) - NGINX & Gunicorn Management

### Data Processing
* [scipy](https://scipy.org/) - Genetic Data Processing
* [numpy](https://numpy.org/) - Genetic Data Processing
* [inbreeding-python](https://github.com/Owen-Dechow/inbreeding-python) - Pedigree Inbreeding Coefficient Calculation

### References
* [Cow Progress](https://cowprogress.com) - Original Simulation Program
* [Net merit as a measure of lifetime profit: 2021 revision](https://www.ars.usda.gov/ARSUserFiles/80420530/Publications/ARR/nmcalc-2021_ARR-NM8.pdf) - PTA Information
* [Genetic Correlations for HOL breed](https://www.ars.usda.gov/arsuserfiles/80420530/publications/arr/nm8%20supplemental%20table_correlations_2021.txt) - Genetic Correlation Information

<p align="center">
    <img src="base/static/media/banner2.webp" alt="cat">
</p>

## Contributing

If you would like to contribute in some way please create an issue, fork the
[repository](https://github.com/Owen-Dechow/herdgen), and create a pull request. When
create a pull request be specific about the changes you have made and ensure you have
tested the program.

No matter the size of your contribution, it is greatly appreciated.

## Documentation

For more information please view the documentation found on the
[Github repository](https://github.com/Owen-Dechow/herdgen/tree/main/docs) or in the
[local repository](/docs/).

<p align="center">
    <img src="base/static/media/banner1.webp" alt="rabbit">
</p>
