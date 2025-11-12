Simple Aurora Archive

You are an expert Python and web developer. Come up with a plan for a static HTML webiste that provides a frontend website for a set of files that track solar activity and timelapses of the sky.  The main purpose of the site is for tracking and viewing the Northern Lights, but it also has daily daytime time lapse videos of the sky to show the clouds.

Here is an example of what the directory looks like.  It is a Linux system and the same 7 days of files always appear with a day of the week filename, but they are overwritten each week with a new version for that day of the weeke.

$ ls -l
total 108808
-rw-r--r-- 1 root root  6070230 Nov  7 06:32 AuroraCam_Friday.mp4
-rw-r--r-- 1 root root  6718724 Nov 10 06:43 AuroraCam_Monday.mp4
-rw-r--r-- 1 root root  5124180 Nov  8 06:34 AuroraCam_Saturday.mp4
-rw-r--r-- 1 root root  5491178 Nov  9 06:39 AuroraCam_Sunday.mp4
-rw-r--r-- 1 root root  3530382 Nov  6 06:28 AuroraCam_Thursday.mp4
-rw-r--r-- 1 root root  4314053 Nov 11 06:44 AuroraCam_Tuesday.mp4
-rw-r--r-- 1 root root  7608011 Nov  5 06:23 AuroraCam_Wednesday.mp4
-rw-r--r-- 1 root root 12690037 Nov  7 18:31 CloudCam_Friday.mp4
-rw-r--r-- 1 root root  3909719 Nov 10 17:59 CloudCam_Monday.mp4
-rw-r--r-- 1 root root  7322536 Nov  8 18:28 CloudCam_Saturday.mp4
-rw-r--r-- 1 root root 12797078 Nov  9 18:30 CloudCam_Sunday.mp4
-rw-r--r-- 1 root root 13721677 Nov  6 18:33 CloudCam_Thursday.mp4
-rw-r--r-- 1 root root  4695537 Nov 11 18:00 CloudCam_Tuesday.mp4
-rw-r--r-- 1 root root 16967069 Nov  5 18:33 CloudCam_Wednesday.mp4
-rw-r--r-- 1 root root    52554 Nov 11 22:17 snapshot.jpg
-rw-r--r-- 1 root root    51601 Nov  7 10:42 SpaceWeather_Friday.gif
-rw-r--r-- 1 root root    49185 Nov 10 11:35 SpaceWeather_Monday.gif
-rw-r--r-- 1 root root    50656 Nov  8 10:31 SpaceWeather_Saturday.gif
-rw-r--r-- 1 root root    49337 Nov  9 11:18 SpaceWeather_Sunday.gif
-rw-r--r-- 1 root root    51386 Nov  6 10:01 SpaceWeather_Thursday.gif
-rw-r--r-- 1 root root    49174 Nov 11 11:35 SpaceWeather_Tuesday.gif
-rw-r--r-- 1 root root    50429 Nov  5 09:54 SpaceWeather_Wednesday.gif


The AuroraCam_<day>.mp4 files are nighttime timelapse videos (360p resolution).
The CloudCam_<day>.mp4 are daytime timelapse videos (360p resolution).
The SpaceWeather_<day>.gif files are images that show the history of the space weather/Kp index for the last 3 days.
snapshot.jpg is the current snapshot of the sky from the camera.

The program needs to be able to examine the files in this directory and output a static HTML site that shows each day's day and night timelapse videos, and the spaceweather history image from that day, with the correct date parsed from the file timestamps.

The site should be generated in the same directory as the files.  It should be attractively designed and easy to use.

The top of the page should have a nice visual display of the current space weather and the 3 day forecast, with information taken from NOAA's Space Weather website https://www.swpc.noaa.gov/

Below the current and forecast space weather conditions should be the 7 day archive of videos and space weather history from the files.  The most recent day should be at the top, with the days becoming progressively older down the page.

Scripts to generate this site should be written in Python with dependency management using uv.

The scripts and template resources for the project can exist anywhere on teh system and need to accept a target directory as an argument.  The target directory will contain the video and image files that the site will be built around.