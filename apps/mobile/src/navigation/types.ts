export type AuthStackParamList = {
  Login: undefined;
};

export type MainStackParamList = {
  Dashboard: undefined;
  GroceryLists: undefined;
  GroceryListDetail: { listId: string };
  Reminders: undefined;
};
