# Menu Component

This is a menu component that displays a list of items.

## Features

- **Item Selection**: Users can select an item from the menu.
- **Visual Feedback**: The selected item is highlighted with a darker shade of its original color.
- **Keyboard Navigation**: Users can navigate and select items using the keyboard (Enter or Space).

## State Management

- `selectedItem`: Stores the currently selected item object.

## Event Handlers

- `handle_select_item`: A memoized callback function to update the `selectedItem` state.
- `handle_key_down`: Handles keyboard events for item selection.

## Rendering

- The `Menu` component maps over the `items` prop to render a `MenuItem` for each item.
- The `MenuItem` component displays the item's label and applies a dynamic background color based on its selection state.
