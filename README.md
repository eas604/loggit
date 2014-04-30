loggit
======

git-based log synchronization scripts for Unix systems in Python, as a demo for class CIS 538.

# Background
For my Operating Systems Concepts and Security class at the University of South Alabama School of Computing, the instructor tasked each student with implementing a proof-of-concept solution to attempt to harden a system. Afterward, we were to discuss whether the change we implemented was feasible, and whether its benefits outweighted its increased system complexity.

I chose to tackle log synchronization on Unix-like systems. Specifically, the ubiquitous `syslog` protocol, as it has several drawbacks:

* By default, messages are transmitted in-the clear, meaning sensitive logs can be intercepted.
  * This is a double-edged sword, as using encryption will introduce overhead.
* Through man-in-the-middle attacks, it may be possible to transmit false messages to the daemon.
* Communication is done via UDP, meaning messages can be lost or arrive out-of-order.
  * This is a double-edged sword, as using TCP will introduce overhead.

There exist a few workarounds for these problems, including piping `syslog` over SSL. However, I wanted to explore the possibility of transmitting the logs securely while retaining a revision history.

## `git` for log synchronization
I decided to investigate the feasibility of transmitting logs to a remote `git` repository via SSH. `git` has a reputation for efficiently detecting deltas within plaintext files in order to maintain revision history and minimize the bytesize of commits and transmissions.

The commits themselves would be automated within a python script running as a simple daemon, watching a given directory for changes, checking the directory for possible log tampering, and sending the deltas to a remote log server.

# Test environment
Commits are tested on two nearly identical Ubuntu Server 13.10 virtual machines: one acting as a server, the other a client. The client machine will push commits to the server at configurable intervals. Furthermore, to benchmark performance under a simulated brute-force login attack via SSH, the client will have a script writing entries to `/var/log/auth.log` as the commits are being sent to the server.

## Usage

### Log committing (as `root`, if tailing `/var/log`)
```sh
python3 loggit.py -i [interval in seconds] user host local_path remote_path
```

### Brute force simulation (as `root`, if writing to `/var/log/auth.log`)
```sh
python3 brute_force.py -i [interval in seconds] log_path
```

# Tampering detection
The python script executes `git diff` to review changes since the last commit. If it spots any removed or changed lines, these lines are logged. Ideally, were this deployed in a production environment, the daemon would send an email alert or something similar, as there's nothing stopping a supposed attacker from also tampering with the daemon's logs.

This implementation may miss some tampering, as there is a slight delay between the `git diff` and `git commit` calls. If a log is tampered with in that window, it will be missed. A more robust solution would base the commit on the `diff` itself, but that will be left to a later revision.

# Performance
On light load, the system performs adequately, with each cycle of tampering detection and commit taking approximately 0.27 seconds. However, under high log activity, the performance degrades with each subsequent iteration. For example, while executing both the brute force simulator and the log commit script simultaneously, with no delay between iterations, I saw performance similar to the following, where the last item is the commit duration in seconds:

    2014-04-24 17:09:26,635 INFO > Changeset committed [...] 1.0090413093566895
    2014-04-24 17:09:29,429 INFO > Changeset committed [...] 2.3560945987701416
    2014-04-24 17:09:33,081 INFO > Changeset committed [...] 2.7702529430389404
    2014-04-24 17:09:37,355 INFO > Changeset committed [...] 3.216939687728882
    2014-04-24 17:09:42,050 INFO > Changeset committed [...] 3.56319522857666
    2014-04-24 17:09:47,379 INFO > Changeset committed [...] 4.02705454826355
    
# Verdict
Bottom line: this rather naive approach performs acceptably only in the lightest load scenarios. It might be usable pushing logs every few seconds on lightly-used, isolated machines on a home network, but has no place on public-facing machines or in the enterprise.
