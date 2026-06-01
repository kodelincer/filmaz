aria2.addUri
aria2.tellStatus
aria2.tellActive
aria2.tellWaiting
aria2.tellStopped

aria2.pause
aria2.pauseAll

aria2.unpause
aria2.unpauseAll

aria2.remove
aria2.forceRemove

aria2.getVersion
aria2.getGlobalStat
----------------------------------

Python code  →  Tool wrapper  →  OpenClaw tool registry  →  Skill uses tool

~/.openclaw/workspace/tools/aria2/
    aria2_add.py
    aria2_status.py
    aria2_health.py

# openclaw restart

or

openclaw.json:

{
  "tools": {
    "aria2_add": {
      "path": "workspace/tools/aria2/aria2_add.py"
    },
    "aria2_status": {
      "path": "workspace/tools/aria2/aria2_status.py"
    },
    "aria2_health": {
      "path": "workspace/tools/aria2/aria2_health.py"
    }
  }
}


==============
addUri()
   ↓
waiting
   ↓
active
   ↓
complete
----------------
active
   ↓
paused
   ↓
active
   ↓
complete
-----------------
active
   ↓
error
-------------
addUri()
The task usually enters:
waiting
or directly:
active
# depending on available download slots (max-concurrent-downloads).
------------------
waiting
Meaning:
The download exists.
The file has not started downloading yet.
It is queued.
------------------
active
Meaning:
Bytes are currently being downloaded.
Retrieve with:
aria2.tellActive
Status:
{
  "status":"active"
}
This is the normal "downloading" state.
--------------
pause()
When you call:

{
  "method":"aria2.pause"
}
The task becomes:
paused
What happens?
Network connections close.
No more bytes are downloaded.
Partial file remains on disk.
Progress is preserved.

Example:
Movie.mkv
50% downloaded
↓
pause
↓
50% still on disk
Nothing is lost.
----------
unpause()   =>>>> resume
When you call:
{
  "method":"aria2.unpause"
}
The task returns to:
active
or
waiting
if the queue is full.

Example:
50% downloaded
↓
pause
↓
unpause
↓
continues from 50%
This is the resume operation.

pause      = stop temporarily
unpause    = resume
-------------------------------------
remove()
When you call:
{
  "method":"aria2.remove"
}

The task is removed from aria2's queue.
Result:
active
↓
removed

What happens?
Download stops immediately.
GID disappears from active/waiting lists.
aria2 forgets the task.

Important:
The partially downloaded file usually remains on disk.

forceRemove()
More aggressive version

remove = graceful stop
forceRemove = kill immediately
---------------------
complete
When download finishes:
active
↓
complete
Retrieve with:
aria2.tellStopped
Status:
{
  "status":"complete"
}
The file is fully downloaded.

-----------------
error
If the download fails:
active
↓
error

Examples:
404 Not Found
Connection timeout
Disk full
Permission denied

Also retrieved through:
aria2.tellStopped

=============================
What should your OpenClaw tools mean?
User Action	      RPC Method	      Result
Start download  	addUri	          creates task
Show progress   	tellStatus	      inspect task
List running    	tellActive	      active tasks
List queued     	tellWaiting	      waiting tasks
Pause	            pause     	      active → paused
Resume          	unpause	          paused → active
Cancel          	remove	          task removed
Force cancel    	forceRemove	      immediate removal
History         	tellStopped	      complete/error/removed
-----------
Download movie => aria2_add

Pause download => aria2_pause

Resume download => aria2_unpause

Cancel download => aria2_remove

Show active downloads => aria2_list_active

Show completed downloads => aria2_list_stopped

show "paused" downloads => tellWaiting()

Download progress => aria2_status
-----------------
One subtle point: "paused" downloads are not returned by tellStopped(). 
They are typically returned via tellWaiting() with status "paused". 
So if you want the agent to find resumable downloads, it should inspect both 
active and waiting lists, not only stopped downloads.