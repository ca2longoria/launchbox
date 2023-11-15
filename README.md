---
# launchbox

It's a lunchbox!  But also a launcher of boxes.  EC2 instances in this case.

---

### Version actively in development

Full history listed in wiki.

#### v0.1_3.4_5.6

Working toward minor version 2
- [x] get network connecting to newly started instance
  - [~] ENC or something, Elastic Network Connection I think?
    - this wasn't it; it was a Subnet auto-assign public ipv4 setting
  - [x] auto-create one on new instance if specified in profile config file
    - new Subnet with autoassign works for public internet connection
- [x] buildup steps, packages
  - [x] packages specified in config file
  - [x] packages actually install
- [ ] buildup steps, git
  - [ ] git clone working
    - [x] https
    - [ ] ssh
      - need this to pull private github repositories
- [x] BUGS
  - [x] terminate() fails when it selects certain instances
    - terminated and shutting-down instances now ignored

Pushing to minor version 3
- [ ] buildup steps, archives
  - [ ] wget/curl archive and extract
  - [ ] S3 archive and extract, or pull whole stored dir



