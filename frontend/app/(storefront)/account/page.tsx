"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ShoppingBag,
  User,
  MapPin,
  Phone,
  Mail,
  Clock,
  Package,
  ChevronRight,
  Loader2,
  ChevronLeft,
  ChevronRight as ChevronRightIcon,
} from "lucide-react";
import { OrderRead, OrderItemRead, PaginatedResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

interface OrderListItem {
  id: string;
  order_number: string;
  grand_total: number;
  order_status: string;
  created_at: string;
  order_items: OrderItemRead[];
}

function OrderStatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    pending: "bg-warning/10 text-warning border-warning/20",
    confirmed: "bg-primary/10 text-primary border-primary/20",
    processing: "bg-blue/10 text-blue border-blue/20",
    shipped: "bg-purple/10 text-purple border-purple/20",
    delivered: "bg-success/10 text-success border-success/20",
    cancelled: "bg-destructive/10 text-destructive border-destructive/20",
    refunded: "bg-muted/10 text-muted border-muted/20",
  };
  return (
    <Badge variant="outline" className={cn("text-xs", variants[status] || variants.pending)}>
      {status}
    </Badge>
  );
}

export default function AccountPage() {
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [activeTab, setActiveTab] = useState<string>("orders");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 20,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const { user } = useAuth();

  const fetchOrders = useCallback(async (page: number = 1) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: "20",
        format: "v2",
      });
      if (statusFilter) {
        params.append("status", statusFilter);
      }
      const data = await apiFetch<PaginatedResponse<OrderRead>>(`/orders?${params.toString()}`);
      if (data) {
        setOrders(data.data);
        setPagination(data.meta);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchOrders(1);
  }, [fetchOrders]);

  const statusLabel: Record<string, string> = {
    pending: "পেন্ডিং",
    confirmed: "কনফার্মড",
    processing: "প্রসেসিং",
    shipped: "শিপ করা হয়েছে",
    delivered: "ডেলিভার্ড",
    cancelled: "বাতিল",
    refunded: "রিফান্ডেড",
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Card className="max-w-4xl mx-auto">
        <CardHeader className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4">
          <div>
            <CardTitle className="text-xl">আপনার অ্যাকাউন্ট</CardTitle>
            <CardDescription>
              অর্ডার হিস্ট্রি এবং প্রোফাইল তথ্য পরিচালনা করুন
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <User className="h-5 w-5" />
            </div>
            <div className="hidden sm:block">
              <p className="font-medium text-foreground">
                {user?.email || "গ্রাহক"}
              </p>
              <p className="text-xs text-muted-foreground">{user?.roles.join(", ") || "customer"}</p>
            </div>
          </div>
        </CardHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full">
            <TabsTrigger
              value="orders"
              className="w-full text-left"
              onClick={() => setActiveTab("orders")}
            >
              <ShoppingBag className="mr-2 h-4 w-4" />
              অর্ডার হিস্ট্রি
            </TabsTrigger>
            <TabsTrigger
              value="profile"
              className="w-full text-left"
              onClick={() => setActiveTab("profile")}
            >
              <User className="mr-2 h-4 w-4" />
              প্রোফাইল
            </TabsTrigger>
          </TabsList>

          <TabsContent value="orders" className="pt-6">
            <div className="space-y-4">
              {error && (
                <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive text-sm">
                  {error}
                </div>
              )}

              {/* Status Filter */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setStatusFilter(null)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                    !statusFilter
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/50"
                  }`}
                >
                  সব
                </button>
                {["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      statusFilter === s
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/50"
                    }`}
                  >
                    {statusLabel[s] || s}
                  </button>
                ))}
              </div>

              {orders.length === 0 && !loading ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                    <ShoppingBag className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium text-foreground">
                    {statusFilter ? `স্ট্যাটস "${statusLabel[statusFilter] || statusFilter}" সহ অর্ডার নেই` : "অর্ডার নেই"}
                  </h3>
                  <p className="text-muted-foreground">
                    {statusFilter ? "অন্য স্ট্যাটস দিয়ে খুঁজুন" : "শপিং শুরু করুন এবং আপনার অর্ডারগুলো ট্র্যাক করুন।"}
                  </p>
                  {!statusFilter && (
                    <Button asChild className="mt-4">
                      <a href="/shop">শপিং শুরু করুন</a>
                    </Button>
                  )}
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    {orders.map((order) => (
                      <Card
                        key={order.id}
                        className="hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => window.location.href = `/account/orders/${order.id}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <p className="font-medium text-foreground">
                                অর্ডার #{order.order_number.slice(-8)}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(order.created_at).toLocaleDateString("bn-BD", {
                                  year: "numeric",
                                  month: "long",
                                  day: "numeric",
                                })}
                              </p>
                            </div>
                            <OrderStatusBadge status={order.order_status} />
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-xs text-muted-foreground">গ্র랜드 টোটাল</p>
                              <p className="font-medium text-foreground">
                                ৳{((typeof order.grand_total === "number" ? order.grand_total : Number(order.grand_total)) ?? 0).toFixed(2)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">আইটেম</p>
                              <p className="font-medium text-foreground">
                                {order.order_items.length}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">স্ট্যাটাস</p>
                              <span className="font-medium text-foreground">
                                {statusLabel[order.order_status] || order.order_status}
                              </span>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center gap-2 text-xs text-primary">
                            <ChevronRight className="h-3 w-3" />
                            বিস্তারিত দেখুন
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Pagination */}
                  {pagination.total_pages > 1 && (
                    <div className="flex items-center justify-center gap-2 pt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fetchOrders(pagination.page - 1)}
                        disabled={!pagination.has_prev}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        পৃষ্ঠা {pagination.page} / {pagination.total_pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fetchOrders(pagination.page + 1)}
                        disabled={!pagination.has_next}
                      >
                        <ChevronRightIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          </TabsContent>

          <TabsContent value="profile" className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">ব্যক্তিগত তথ্য</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">নাম</span>
                      <span className="text-sm text-foreground">{user?.email?.split("@")[0] || "গ্রাহক"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">ইমেইল</span>
                      <span className="text-sm text-foreground truncate max-w-xs">{user?.email || ""}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">রোল</span>
                      <Badge variant="secondary" className="text-xs">
                        {user?.roles.join(", ") || "customer"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">যোগাযোগ</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium text-foreground">ফোন নম্বর</p>
                        <p className="text-xs text-muted-foreground">প্রোফাইলে যোগ করতে হবে</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium text-foreground">ইমেইল</p>
                        <p className="text-xs text-muted-foreground">{user?.email || ""}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium text-foreground">ঠিকানা</p>
                        <p className="text-xs text-muted-foreground">কোনো ঠিকানা সংরক্ষিত নেই</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}