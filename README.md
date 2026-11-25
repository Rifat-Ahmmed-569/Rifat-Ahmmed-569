<!-- BENCH:START -->
<!-- OPTION A: Paste your bare GitHub user-attachment .mp4 URL on the line below for native autoplay -->
https://github.com/user-attachments/assets/YOUR_UPLOADED_MP4_ID_HERE

<!-- OPTION B: Or delete Option A above and uncomment the block below to use a clickable animated preview linking to your Facebook Reel -->
<!--
[![Hardware Bench Demo](assets/bench-demo.webp)](https://www.facebook.com/reel/1027786212995721)
-->
<!-- BENCH:END -->

I build robots and the embedded systems underneath them: firmware, sensors, motor control, and the glue that makes software and hardware agree with each other. I like working at the layer where things actually fail. The debugging is painful, and that's where the fun is.

**How I work**

- **Go one layer down.** If I don't understand *why* it works, I don't trust that it works.
- **Debugging is the job, not an interruption to it.** A noisy ground, a race in an ISR, a sensor that lies at 40 °C—that's the part I enjoy.
- **Reliable beats impressive.** Working once is a demo. Working every time is engineering.
- **Build with people.** Hard problems get tractable on teams where saying *"I broke it"* is safe. I try to build that kind of team.

### On the bench

<!-- PROJECTS:START -->
#### [‹Build name›](#)
‹One sentence: the problem, the machine, the result.›  
<sub>‹MCU› · ‹framework› · ‹sensors / comms› &nbsp;·&nbsp; built ‹year› → documented ‹year› &nbsp;·&nbsp; ‹solo build / led a team of N›</sub>  
<sub><code>evidence</code> &nbsp;■ schematic &nbsp; ■ firmware &nbsp; □ mechanical &nbsp; ■ test data &nbsp; □ demo</sub>
<!-- PROJECTS:END -->

<!-- ARCHIVE:START -->
<!-- ARCHIVE:END -->

### Signal

<!-- SIGNAL:START -->
<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/signal-light.svg">
  <img src="assets/signal-dark.svg" width="100%" alt="Weekly contribution signal and commit share by domain, last 52 weeks">
</picture>
<!-- SIGNAL:END -->

<sub>**How to read this:** The trace counts commits, pull requests, issues, and reviews per week. It shows *presence*, not quality: a week spent chasing one I²C bug can produce two commits. Quality is in the evidence row under each build above.</sub>

### Stack, from silicon up

```text
hardware    ‹boards, sensors, actuators, PCB tool you actually use›
firmware    ‹languages · MCU families · RTOS / frameworks›
interfaces  ‹UART · I²C · SPI · CAN · PWM — only the ones you've debugged on a scope›
software    ‹Python · ROS 2 · OpenCV … only what you've shipped›
bench       ‹oscilloscope · logic analyzer · PlatformIO · …›
