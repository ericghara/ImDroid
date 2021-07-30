<h2>ImDroid</h2>

<h3>Overview</h3>
ImDroid allows iPhone users to harmoniously share photos with their Android friends by converting photos into a more Android friendly format.  ImDroid works quickly, utilizing multithreading to significantly reduce conversion speed vs. most common image converters. 
<br><br>
To "Androidize" photos ImDroid does 2 things:
<ol>
<li>Convert the image file from HEIC to JPG format</li>
<li>Rename the photo based on the date it was taken (instead of sequentially)</li>
</ol>


<h3>What's under the hood?</h3>

* File conversion and EXIF access is powered by Wand (an ImageMagick binding) 
* UI is built using Qt
* Multithreading is implemented using QtThread methods

