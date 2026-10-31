import { RestaurantEditor } from "@/components/admin/restaurant-editor";

export default async function EditRestaurantPage(props: PageProps<"/admin/restaurants/[id]">) {
  const { id } = await props.params;
  return <RestaurantEditor restaurantId={Number(id)} />;
}
