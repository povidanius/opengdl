This is a Python app for a free, open-source personal numismatic catalogue of coins from the Grand Duchy of Lithuania and the Republic of Lithuania, designed to run locally on a collector’s PC. It is almost entirely coded using Claude Code. Still a very early version, but you may find it useful for organising your collection.

This project is currently a work in progress - this version may not be fully compatible with previous or future versions, so if you are using it for your collection, I recommend backing up your catalogue before pulling future updates. At this stage, only publicly available images and sources (from Wikipedia) have been used. With permission from the respective authors, additional graphical material may be included in the future.

How to run:
- 0.)  Open a terminal (Linux) or Command Prompt (Windows, on Windows OS not tested yet)
- 1.) git clone https://github.com/povidanius/opengdl/
- 2.) cd opengdl
- 3.) docker build -t coin-collection .
- 4.) Run the container:
   ```bash
   docker run -d --name coins \
  -p 5000:5000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/uploads:/app/uploads" \
  coin-collection
- 5.) Point your web browser to `http://127.0.0.1:5000/`
- 6.) To stop the running container: docker stop coins
- 7.) To start it: docker start coins
- 8.) To remove it: docker rm coins
- 9.) consult: README.txt for more information

Also, you should install git and docker, in order to clone this repository, and build and run docker image of this app.


Screenshots:

<img src="Screenshot%20from%202026-04-30%2022-13-23.png" alt="Example 1" title="Example 1" width="50%">

<img src="Screenshot%20from%202026-04-30%2022-13-35.png" alt="Example 2" title="Example 2" width="50%">




## Catalogue References and Books about Lithuanian Numismatics

1. **E. Ivanauskas** (2013). *Coins and Bars of Lithuania 1236–2012 / Монеты и слитки Литвы 1236–2012*. Kaunas: Eugenijus Ivanauskas.  
   ISBNs: `978-9955-772-48-4`, `978-9955-772-49-1`, `978-9955-772-50-7`  
   Link: [MDL Coins](https://www.mdlcoins.lt/parduotuve/literatura/katalogas-coins-and-bars-of-lithuania-1236-2012/)


2. **E. Česnulis and E. Ivanauskas** (2024). *Lietuviškos Gediminaičių monetos, 1345–1492 m.* Vilnius: Netimeras.  
   ISBN: `978-609-95987-8-9`  
   Links: [Knygos.lt](https://www.knygos.lt/lt/knygos/lietuviskos-gediminaiciu-monetos--1345-1492/), [MDL Coins](https://www.mdlcoins.lt/parduotuve/literatura/knyga-katalogas-lietuviskos-gediminaiciu-monetos-1345-1492-m/)

3. **D. Huletski and G. Bagdonas** (2025). *Lithuanian Coins 1495–1536. Second Edition*.  
    ISBN: `978-609-417-285-4`  
    Link: [MDL Coins](https://www.mdlcoins.lt/parduotuve/literatura/katalogas-lithuanian-coins-1495-1536-second-edition/)
       
4. **D. Huletski** (2022). *Lithuanian Grand Ducal Coins before 1401*. Vilnius: Baltijos kopija.  
   ISBN: `978-609-417-240-3`  
   Links: [Sena.lt](https://www.sena.lt/istorija/lithuanian-grand-ducal-coins-before-1401/2351092), [DeaMoneta](https://www.deamoneta.com/shop/item/huletski-lithuanian-grand-ducal-coins-before-1401)
   
5. **D. Huletski and S. Liszewski** (2019). *Lithuanian Counterstamps, 1421–1481: On the Golden Horde’s Silvers*. Vilnius: Petro ofsetas.  
   ISBN: `978-609-420-665-8`  
   Links: [Knygos.lt](https://www.knygos.lt/lt/knygos/lithuanian-counterstamps--1421-1481--on-the-golden-hordes-silvers/), [NumisLit](https://www.numislit.com/pages/books/5582/dzmitry-huletski-slawomir-liszewski/lithuanian-counterstamps-1421-1481-on-the-golden-hordes-silvers)   

6. **E. Česnulis and E. Ivanauskas** (2018). *Lithuanian Coins of Sigismund August, 1545–1571*. Revised 2nd ed. Vilnius: Netimeras.  
   ISBN: `978-609-95987-1-0`  
   Link: [Knygos.lt](https://www.knygos.lt/lt/knygos/lithuanian-coins-of-sigismund-august--1545-1571/)

7. **D. Grimalauskaitė and E. Remecas** (2020). *Money in Lithuania*. Vilnius: Lietuvos nacionalinis muziejus.  
   ISBN: `978-609-478-049-3`  
   Link: [Knygos.lt](https://www.knygos.lt/lt/knygos/money-in-lithuania/)

## Video Resources

- **Vilnius Coinage of Alexander and Sigismund the Old**. YouTube channel.  
  Link: [YouTube](https://www.youtube.com/@vilniuscoinageofalexandera4032)   
  
