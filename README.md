# klepp.me
*A service to share clips among friends, while owning and managing our own data*  

### Stack

**Storage**: [gg.klepp.me](https://gg.klepp.me) -> TLS through AWS Certificate Manager -> AWS Cloudfront CDN -> AWS S3 bucket    
**API**: [api.klepp.me](https://api.klepp.me/docs) -> TLS through Heroku -> Hosted on Heroku -> FastAPI -> [validate tokens](app/api/security.py) -> [S3 bucket](app/api/api_v1/endpoints/file.py)    
**Authentication** [auth.klepp.me](https://auth.klepp.me) -> TLS through AWS Certificate Manager -> AWS Cognito -> Validating tokens in backend  
**Frontend**: [klepp.me -  Soon™](https://klepp.me) - x -> TLS -> React frontend -> Cognito auth -> Requests to the API


## What?
[klepp.me](https://klepp.me) tries to be a [streamable.com](https://streamable.com/) / [pomf.cat](https://pomf.cat/) clone, 
which integrates natively with [`ShareX`](https://getsharex.com/). 
Any screenshot or video recorded through this program is automatically be uploaded to `gg.klepp.me`. When the file has been
uploaded, a URL with a link to the resource is automatically stored in your clipboard.  
This file can be shared with friends and viewed directly in your browser. There is no size limit on any file.

The API allows the user to list all video files from all users. If a user don't want a video to be listed, the user can hide their own video from this list.
The user can at any point unhide/show the video again to allow others to discover it. All users can upload and delete their own files, even those
uploaded through ShareX. 

The frontend allow you to list and view the latest clips, as well as managing your own files as described above.

TL;DR:   
**ShareX support**: Upload clips, files and images directly to the s3 bucket. Share `gg.klepp.me`-links directly.  
**API**: Upload, delete and manage your own files. List all files that are not in a hidden folder. Hide files you don't want to be listed from the list-API.  
**Frontend**: View clips from all users, sorted on newest  

## Why?

I started using `pomf.cat`, until I unfortunately uploaded a screenshot of my desktop with personal information in it. (Using ShareX, so all screenshots are automatically uploaded)
Since `pomf.cat` has no users, there was no way for me to delete this screenshot without mailing the owners of the site hoping they would listen (they did). 
At this point, I knew I could never use pomf.cat or untrusted service for this purpose again.  
Lately, I've swapped to `streamable.com` for video uploading of short gaming clips among friends. The size limit is better, but 13 dollar per month (per user) for 
storage of short clips seemed a bit steep.

We also share these clips on TeamSpeak, and if you're not online, you won't see the clip. It feels impossible to find an older clip too, and 
you don't really know for how long it will stay. This won't be a problem longer, any one of us can view any video uploaded through the frontend. :)

TL;DR: Trust issues to external sites, 13 dollar per user at streamable was too much. We also wanted a unified dashboard where we could watch all the clips in our friend group.

## But klepp..?
Yes, we tend to yell "CLIP!" or "KLEPP!" whenever someone does something we think should be clipped (ShadowPlay) and shared after a game :)