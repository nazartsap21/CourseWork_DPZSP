import { RestaurantView } from "@/components/restaurant/restaurant-view";

export default async function RestaurantPage(props: PageProps<"/restaurants/[id]">) {
  const { id } = await props.params;
  return <RestaurantView restaurantId={Number(id)} />;
}
