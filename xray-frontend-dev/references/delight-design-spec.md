# Delight Design Spec

## Core Rule

Prefer Delight design tokens and existing variables instead of inventing new raw values.

When writing styles:
- Prefer existing variables over hard-coded color, spacing, radius, shadow, opacity, and typography values.
- Reuse current Delight tokens first, then reuse page-level existing styles, and only add new values when there is no suitable token.
- Do not casually generate new hex, rgb, rgba, px, or timing values if a Delight variable already expresses the same intent.
- Keep visual consistency with existing Delight components before pursuing custom decoration.

## Variable-First Guidance

Use semantic variables first:
- Interactive primary actions: prefer `$color-primary`, `$color-primary-hover`, `$color-primary-pressing`
- Warning states: prefer `$color-warning*`
- Danger states: prefer `$color-danger*`
- Info states: prefer `$color-info*`
- Success states: prefer `$color-success*`
- Text hierarchy: prefer `$color-text-title`, `$color-text-paragraph`, `$color-text-description`, `$color-text-placeholder`, `$color-text-disabled`
- Borders and dividers: prefer `$color-border-default`, `$color-border-light`, `$border-default`, `$border-divider`
- Fill and background: prefer `$color-bg`, `$color-bg-1`, `$color-fill`, `$color-fill-hover`, `$color-fill-opaque`
- Spacing: prefer `$size-space-small`, `$size-space-default`, `$size-space-large`
- Radius: prefer `$size-radius-small`, `$size-radius-default`, `$size-radius-large`, `$size-radius-largest`
- Typography: prefer `$size-text-*`, `$size-text-line-height-*`, `$size-text-font-weight-*`
- Shadow: prefer `$shadow-default`, `$shadow-portal`, `$shadow-drawer`
- Motion: prefer `$time-transition-fast`, `$time-transition-default`, `$time-transition-slow`, `$standard-easing`

Avoid patterns like:
- Writing ad hoc values such as `#386bff`, `rgba(0, 0, 0, 0.08)`, `12px`, `16px`, `4px`, `6px` directly into new styles when matching Delight tokens already exist
- Introducing slightly different near-duplicate values that make the UI drift over time

## Token Reference

```stylus
// variables
$color-primary = $color-blue-6
$color-primary-hover = $color-blue-7
$color-primary-pressing = $color-blue-8
$color-primary-disabled = $color-blue-3
$color-primary-light = $color-blue-1
$color-primary-light-hover = $color-blue-2
$color-primary-light-pressing = $color-blue-3

$color-warning = $color-orange-6
$color-warning-hover = $color-orange-7
$color-warning-pressing = $color-orange-8
$color-warning-disabled = $color-orange-3
$color-warning-light = $color-orange-1
$color-warning-light-hover = $color-orange-2
$color-warning-light-pressing = $color-orange-3

$color-danger = $color-red-6
$color-danger-hover = $color-red-7
$color-danger-pressing = $color-red-8
$color-danger-disabled = $color-red-3
$color-danger-light = $color-red-1
$color-danger-light-hover = $color-red-2
$color-danger-light-pressing = $color-red-3

$color-info = $color-blue-6
$color-info-hover = $color-blue-7
$color-info-pressing = $color-blue-8
$color-info-disabled = $color-blue-3
$color-info-light = $color-blue-1
$color-info-light-hover = $color-blue-2
$color-info-light-pressing = $color-blue-3

$color-success = $color-green-6
$color-success-hover = $color-green-7
$color-success-pressing = $color-green-8
$color-success-disabled = $color-green-3
$color-success-light = $color-green-1
$color-success-light-hover = $color-green-2
$color-success-light-pressing = $color-green-3

$color-transparent = transparent
$color-current = currentColor
$color-white = rgb(255, 255, 255)
$color-black = rgb(0, 0, 0)

$color-bg- = rgba(245, 245, 245, 1)
$color-bg = rgba(255, 255, 255, 1)
$color-bg-1 = rgba(250, 250, 250, 1)
$color-bg-2 = rgba(255, 255, 255, 1)

$color-dark-bg = rgba(61, 61, 61, 1)
$color-mask-light = rgba(1, 1, 4, 0.8)
$color-mask-loading = rgba(255, 255, 255, 0.7)

$color-brand-0 = rgb(255, 247, 246)
$color-brand-1 = rgb(255, 237, 235)
$color-brand-2 = rgb(255, 216, 213)
$color-brand-3 = rgb(255, 183, 180)
$color-brand-4 = rgb(255, 141, 142)
$color-brand-5 = rgb(255, 89, 99)
$color-brand-6 = rgb(255, 36, 66)
$color-brand-7 = rgb(219, 0, 49)
$color-brand-8 = rgb(160, 0, 32)
$color-brand-9 = rgb(130, 0, 21)
$color-brand-10 = rgb(72, 0, 9)

$color-grey-0 = rgba(250, 250, 250, 1)
$color-grey-1 = rgba(243, 243, 243, 1)
$color-grey-2 = rgba(226, 226, 226, 1)
$color-grey-3 = rgba(204, 204, 204, 1)
$color-grey-4 = rgba(180, 180, 180, 1)
$color-grey-5 = rgba(157, 157, 157, 1)
$color-grey-6 = rgba(136, 136, 136, 1)
$color-grey-7 = rgba(116, 116, 116, 1)
$color-grey-8 = rgba(97, 97, 97, 1)
$color-grey-9 = rgba(78, 78, 78, 1)
$color-grey-10 = rgba(61, 61, 61, 1)

$color-orange-0 = rgb(255, 247, 243)
$color-orange-1 = rgb(255, 238, 229)
$color-orange-2 = rgb(254, 223, 206)
$color-orange-3 = rgb(255, 193, 160)
$color-orange-4 = rgb(255, 162, 117)
$color-orange-5 = rgb(255, 131, 79)
$color-orange-6 = rgb(253, 99, 33)
$color-orange-7 = rgb(228, 84, 16)
$color-orange-8 = rgb(189, 64, 0)
$color-orange-9 = rgb(137, 44, 0)
$color-orange-10 = rgb(95, 32, 0)

$color-red-0 = rgb(255, 248, 250)
$color-red-1 = rgb(255, 236, 242)
$color-red-2 = rgb(255, 216, 228)
$color-red-3 = rgb(254, 177, 195)
$color-red-4 = rgb(255, 139, 161)
$color-red-5 = rgb(253, 100, 128)
$color-red-6 = rgb(251, 51, 103)
$color-red-7 = rgb(214, 33, 77)
$color-red-8 = rgb(172, 18, 58)
$color-red-9 = rgb(120, 15, 39)
$color-red-10 = rgb(83, 0, 27)

$color-pink-0 = rgb(254, 246, 251)
$color-pink-1 = rgb(253, 237, 248)
$color-pink-2 = rgb(253, 215, 240)
$color-pink-3 = rgb(251, 174, 226)
$color-pink-4 = rgb(250, 134, 212)
$color-pink-5 = rgb(241, 93, 192)
$color-pink-6 = rgb(213, 61, 162)
$color-pink-7 = rgb(177, 41, 130)
$color-pink-8 = rgb(137, 29, 100)
$color-pink-9 = rgb(96, 21, 71)
$color-pink-10 = rgb(73, 1, 55)

$color-violet-0 = rgb(252, 248, 253)
$color-violet-1 = rgb(249, 238, 251)
$color-violet-2 = rgb(242, 218, 248)
$color-violet-3 = rgb(230, 180, 243)
$color-violet-4 = rgb(217, 144, 235)
$color-violet-5 = rgb(200, 108, 222)
$color-violet-6 = rgb(175, 74, 200)
$color-violet-7 = rgb(144, 52, 167)
$color-violet-8 = rgb(111, 37, 129)
$color-violet-9 = rgb(76, 24, 89)
$color-violet-10 = rgb(59, 8, 72)

$color-purple-0 = rgb(250, 248, 255)
$color-purple-1 = rgb(243, 238, 255)
$color-purple-2 = rgb(232, 220, 255)
$color-purple-3 = rgb(210, 187, 255)
$color-purple-4 = rgb(187, 153, 255)
$color-purple-5 = rgb(162, 120, 254)
$color-purple-6 = rgb(135, 89, 236)
$color-purple-7 = rgb(108, 65, 200)
$color-purple-8 = rgb(82, 47, 157)
$color-purple-9 = rgb(56, 32, 108)
$color-purple-10 = rgb(39, 16, 81)

$color-blue-0 = rgb(248, 250, 255)
$color-blue-1 = rgb(236, 240, 255)
$color-blue-2 = rgb(212, 223, 255)
$color-blue-3 = rgb(178, 200, 255)
$color-blue-4 = rgb(127, 163, 255)
$color-blue-5 = rgb(95, 135, 254)
$color-blue-6 = rgb(56, 107, 255)
$color-blue-7 = rgb(40, 89, 228)
$color-blue-8 = rgb(36, 75, 188)
$color-blue-9 = rgb(21, 55, 143)
$color-blue-10 = rgb(9, 33, 95)

$color-cyan-0 = rgb(242, 251, 254)
$color-cyan-1 = rgb(231, 246, 254)
$color-cyan-2 = rgb(207, 237, 253)
$color-cyan-3 = rgb(155, 218, 251)
$color-cyan-4 = rgb(104, 195, 243)
$color-cyan-5 = rgb(38, 175, 231)
$color-cyan-6 = rgb(10, 143, 201)
$color-cyan-7 = rgb(9, 108, 156)
$color-cyan-8 = rgb(13, 83, 120)
$color-cyan-9 = rgb(3, 58, 86)
$color-cyan-10 = rgb(3, 39, 57)

$color-teal-0 = rgb(245, 251, 250)
$color-teal-1 = rgb(232, 247, 246)
$color-teal-2 = rgb(208, 238, 235)
$color-teal-3 = rgb(157, 222, 216)
$color-teal-4 = rgb(115, 203, 195)
$color-teal-5 = rgb(0, 183, 169)
$color-teal-6 = rgb(0, 154, 141)
$color-teal-7 = rgb(0, 126, 115)
$color-teal-8 = rgb(0, 99, 90)
$color-teal-9 = rgb(0, 73, 66)
$color-teal-10 = rgb(1, 43, 39)

$color-green-0 = rgb(239, 253, 244)
$color-green-1 = rgb(225, 250, 235)
$color-green-2 = rgb(194, 243, 214)
$color-green-3 = rgb(140, 232, 170)
$color-green-4 = rgb(80, 211, 127)
$color-green-5 = rgb(33, 196, 99)
$color-green-6 = rgb(0, 171, 70)
$color-green-7 = rgb(0, 143, 59)
$color-green-8 = rgb(0, 110, 48)
$color-green-9 = rgb(0, 79, 33)
$color-green-10 = rgb(4, 49, 22)

$color-yellow-0 = rgb(255, 250, 222)
$color-yellow-1 = rgb(252, 244, 207)
$color-yellow-2 = rgb(253, 239, 171)
$color-yellow-3 = rgb(255, 232, 140)
$color-yellow-4 = rgb(252, 222, 108)
$color-yellow-5 = rgb(255, 211, 47)
$color-yellow-6 = rgb(247, 198, 0)
$color-yellow-7 = rgb(222, 178, 0)
$color-yellow-8 = rgb(188, 144, 0)
$color-yellow-9 = rgb(154, 118, 0)
$color-yellow-10 = rgb(122, 93, 0)

$contrast-0 = rgba(255, 255, 255, 1)
$contrast-12 = rgba(0, 0, 0, 0.08)
$contrast-15 = rgba(0, 0, 0, 0.18)
$contrast-18 = rgba(0, 0, 0, 0.24)
$contrast-21 = rgba(0, 0, 0, 0.3)
$contrast-full = rgba(0, 0, 0, 1)

$opacity-fill = 0.03
$opacity-fill-hover = 0.05
$opacity-fill-pressing = 0.08
$opacity-fill-disabled = 0.02
$opacity-fill-light = 0
$opacity-fill-black = 0.8
$opacity-fill-mask = 0.8

$opacity-muted = 0.67
$opacity-muted-hover = 0.85
$opacity-muted-pressing = 1
$opacity-muted-disabled = 0.28
$opacity-muted-loading = $opacity-muted-disabled

$color-fill = rgba(0, 0, 0, 0.03)
$color-fill-black = rgb(0, 0, 0, 1)
$color-fill-mask = rgba(0, 0, 0, 0.8)
$color-fill-hover = rgba(0, 0, 0, 0.05)
$color-fill-pressing = rgba(0, 0, 0, 0.08)
$color-fill-disabled = rgba(0, 0, 0, 0.02)
$color-fill-light = rgba(0, 0, 0, 0)
$color-fill-opaque = rgba(247, 247, 247, 1)
$color-fill-hover-opaque = rgba(242, 242, 242, 1)
$color-fill-pressing-opaque = rgba(235, 235, 238, 1)
$color-fill-disabled-opaque = rgba(250, 250, 250, 1)
$color-fill-light-opaque = rgba(0, 0, 0, 0)

$color-line-divider = rgba(0, 0, 0, 0.08)
$color-line-stroke = rgba(0, 0, 0, 0.10)

$opacity-text-title = 0.9
$opacity-text-paragraph = 0.67
$opacity-text-description = 0.47
$opacity-text-placeholder = 0.52
$opacity-text-disabled = 0.29

$color-text-title = rgba(0, 0, 0, 0.85)
$color-text-paragraph = rgba(0, 0, 0, 0.7)
$color-text-description = rgba(0, 0, 0, 0.53)
$color-text-placeholder = rgba(0, 0, 0, 0.42)
$color-text-disabled = rgba(0, 0, 0, 0.2)

$size-icon-small = 12px
$size-icon-default = 16px
$size-icon-large = 20px
$size-icon-extra-large = 24px

$size-text-small = 12px
$size-text-default = 14px
$size-text-h6 = 16px
$size-text-h5 = 18px
$size-text-h4 = 20px
$size-text-h3 = 24px
$size-text-h2 = 28px
$size-text-h1 = 32px

$size-text-line-height-small = 20px
$size-text-line-height-default = 22px
$size-text-line-height-h6 = 24px
$size-text-line-height-h5 = 26px
$size-text-line-height-h4 = 28px
$size-text-line-height-h3 = 36px
$size-text-line-height-h2 = 40px
$size-text-line-height-h1 = 44px

$size-text-font-weight-default = 400
$size-text-font-weight-bold = 500
$size-text-font-weight-heavy = 600

$size-space-step-small = 2px
$size-space-step-default = 4px
$size-space-small = ($size-space-step-default * 2)
$size-space-default = ($size-space-step-default * 3)
$size-space-large = ($size-space-step-default * 4)

$size-width-small = 100px
$size-width-default = 160px
$size-width-large = 240px

$size-form-line-height-default = 32px
$size-form-title-width-default = 178px
$size-form-item-width-extra-small = 104px
$size-form-item-width-small = 216px
$size-form-item-width-default = 328px
$size-form-item-width-large = 440px
$size-form-item-width-extra-large = 552px

$time-transition-fast = .1s
$time-transition-default = .15s
$time-transition-slow = .24s
$time-transition-extra-slow = .4s
$standard-easing = cubic-bezier(0.2, 0, 0.38, 0.9)
$entrance-easing = cubic-bezier(0, 0, 0.38, 0.9)
$exit-easing = cubic-bezier(0.2, 0, 1, 0.9)
$time-transition-short = .1s
$time-transition-long = .6s

$size-radius-small = 2px
$size-radius-medium = 3px
$size-radius-default = 4px
$size-radius-large = 6px
$size-radius-super-large = 8px
$size-radius-largest = 999px

$size-border-default = 1px
$size-border-large-default = 2px

$size-padding-small = 4px
$size-padding-horizontal-small = 2px
$size-padding-vertical-small = 8px

$style-border-default = solid
$opacity-border-default = 0.1
$opacity-border-light = 0.05
$opacity-border-divider = 0.08

$color-border-default = rgba(0, 0, 0, $opacity-border-default)
$color-border-light = rgba(0, 0, 0, $opacity-border-light)
$color-border-divider = rgba(0, 0, 0, $opacity-border-divider)
$color-border-focus = $color-blue-3

$border-default = $size-border-default $style-border-default $color-border-default
$border-light = $size-border-default $style-border-default $color-border-light
$border-divider = $size-border-default $style-border-default $color-border-divider
$border-focus = $size-border-large-default $style-border-default $color-border-focus

$shadow-none = 0 0 0 0 transparent
$shadow-drawer = 0 9px 20px 0 rgba(0, 0, 0, 0.09)
$shadow-display = rgba(0, 0, 0, 0.12) 0 8px 20px, rgba(0, 0, 0, 0.2) 0 0 1px
$shadow-focus = 0 20px 32px 0 rgba(0, 0, 0, 0.12), 0 0 1px 0 rgba(0, 0, 0, 0.2)
$shadow-inset = 0 1px 2px 0 rgba(0, 0, 0, 0.08), 0 0 1px 0 rgba(0, 0, 0, 0.2)
$shadow-inset-reverse = 0 -1px 2px 0 rgba(0, 0, 0, 0.08), 0 0 1px 0 rgba(0, 0, 0, 0.2)
$popover-filter-shadow = drop-shadow(0 0px 0.6px rgba(0,0,0,.08))
$popover-shadow = 0px 8px 12px 0px rgba(0,0,0,.12)
$tooltip-shadow = 0px 8px 20px 0px rgba(0, 0, 0, 0.12), 0px 0px 1px 0px rgba(0, 0, 0, 0.20)
```

## Practical Rule

Before adding a new style value, check in this order:
1. Whether a Delight component already solves the problem
2. Whether an existing token in this file already expresses the needed semantic meaning
3. Whether the current page already has a local pattern that is intentionally aligned with Delight

If one of the above is true, reuse it instead of creating a new value.
