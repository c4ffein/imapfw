# [imapfw](https://github.com/c4ffein/imapfw)

**imapfw is a simple and powerful framework to work with mails.**

That fork comes as a replacement for the [original version by the OfflineIMAP team](https://github.com/OfflineIMAP/imapfw) that already aimed to replace the [OfflineIMAP syncer](https://github.com/OfflineIMAP/offlineimap).

[See changes](#changes-from-original-version)
<!-- **Check out the [official website][website] to get last news *([RSS][feed])* about imapfw.** -->
<!--Also, we have room at
[![Gitter](https://badges.gitter.im/c4ffein/imapfw.svg)](https://gitter.im/c4ffein/imapfw?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
for more instant chatting.-->

<!--
TODO - c4ffein : use special shield instead
[![Latest release](https://img.shields.io/badge/latest release-v0.020-blue.svg)](https://github.com/c4ffein/imapfw/releases)
-->


<table>
  <tr>    <td> Original Author </td>    <td> Nicolas Sebrecht                                </td>    </tr>
  <tr>    <td> Fork Author     </td>    <td> <a href="http://github.com/c4ffein">c4ffein</a> </td>    </tr>
  <tr>    <td> Source          </td>    <td> http://github.com/c4ffein/imapfw                </td>    </tr>
  <!--tr> <td> Website         </td>    <td> http://imapfw.c4ffein.dev                       </td>  </tr-->
  <tr>    <td> License         </td>    <td> The MIT License (MIT)                           </td>    </tr>
  <tr>    <td> Status          </td>    <td> <i> Work In Progress </i>                       </td>    </tr>
</table>

<!--
* [![Build Status: "master" branch](https://travis-ci.org/c4ffein/imapfw.svg?branch=master)](https://travis-ci.org/c4ffein/imapfw) (master)
* [![codecov.io](https://codecov.io/github/c4ffein/imapfw/coverage.svg?branch=master)](https://codecov.io/github/c4ffein/imapfw?branch=master) (master)
* [![Coverage Status](https://coveralls.io/repos/github/c4ffein/imapfw/badge.svg?branch=master)](https://coveralls.io/github/c4ffein/imapfw?branch=master) (master)
* [![Build Status: "next" branch](https://travis-ci.org/c4ffein/imapfw.svg?branch=next)](https://travis-ci.org/c4ffein/imapfw) (next)
* [![codecov.io "next" branch](https://codecov.io/github/c4ffein/imapfw/coverage.svg?branch=next)](https://codecov.io/github/c4ffein/imapfw?branch=next) (next)
* [![Coverage Status "next" branch](https://coveralls.io/repos/github/c4ffein/imapfw/badge.svg?branch=next)](https://coveralls.io/github/c4ffein/imapfw?branch=next) (next)
-->

<!--
![demo](https://raw.githubusercontent.com/OfflineIMAP/imapfw.github.io/gh-pages/images/imapfw.gif)
-->

## Features

#### Scalable

As a framework, imapfw allows you to take control on what gets done:

* Embedded actions (softwares) requiring to write few to no Python code at all.
* For more control, a dedicated API allows to redefine the key parts of the frame in one file (called the *rascal*).
* Finally, most experienced users might rather directly import one or more modules and use them to write full
  softwares, using the framework as a "master-library": imapfw is written with **separation of concerns** in mind.

The choice of the level of control is left to the user.

#### All batteries included

The framework is intended to provide everything is needed.
If any key library is missing, it's welcome to make requests.

#### Simple

imapfw provides nice embedded actions. They can be used like any other software sharing the same purpose.

#### Fast

Mainly relying on UIDs greatly helps to be fast.

Also, imapfw is designed to be fully concurrent.
It even let the choice of the concurrency backend (multiprocessing or threading, for now).
To take real advantage of this, implementation is made asynchronous almost everywhere.

#### Good documentation

Providing good documentation will be a concern.

<!--
#### Quality

* Testing the framework is done with both static and dynamic testing. Each is used where it's the most relevant:
  - low-level code and modules have unit tests;
  - features like *actions* have black box tests.

* Continous intergration is done with [Travis CI][travis].

* The project is developed with a proven release cycle and release candidates.
-->

#### Code

That fork of imapfw relies on one of the latest Python 3 versions to the fork date, 3.9,
as it brought usefule new features.


## Requirements

* Python 3 (starting from v3.9)


## Status

imapfw is **WORK IN PROGRESS**. Running imapfw should not hurt but all the features are not yet implemented.
This is still early stage of development.

Last WIP is in the [`next`branch](https://github.com/c4ffein/imapfw/tree/next). 
PR and Issues are open.

### Roadmap
- Update imaplib2 : https://github.com/jazzband/imaplib2/blob/master/imaplib2/imaplib2.py, port timeout on socket modification, on both ssl and standard version as we modified `open_socket`
- Secure paths
- Documentation in Markdown
- Import [initial wiki](https://github.com/OfflineIMAP/imapfw/wiki) in the documentation
- Black / Flake8

### Changes from original version
- We don't want to use Interface classes, this is Python not Java, [KISS](https://en.wikipedia.org/wiki/KISS_principle)
- Can use TLS, or not, tries to use TLS by default
- Quick-patched imaplib2 to allow timeout even for first connection
- Tries to use instances and not on-the-fly built classes as much as possible
