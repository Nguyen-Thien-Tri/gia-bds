import Header from "../../components/Header";
import HeroSection from "./components/HeroSection";
import BarChartsSection from "./components/BarChartsSection";
import AnalyticsSection from "./components/AnalyticsSection";
import FeaturesSection from "./components/FeaturesSection";
import TargetUsersSection from "./components/TargetUsersSection";
import UserTestimonials from "./components/UserTestimonials";
import Footer from "../../components/Footer";
import SEOTags from "./components/SEOTags";
import GoogleTag from "../../components/GoogleTag";
import { Helmet } from "react-helmet-async";

function TrangChu() {
  return (
    <>
      <Helmet>
        <title>
          Thống kê thị trường giá bất động sản tại Việt Nam |
          giabatdongsan.info.vn
        </title>
        <meta
          name="description"
          content="Nền tảng phân tích dữ liệu toàn diện về thị trường bất động sản Việt Nam. Cập nhật biểu đồ giá ban, giá thuê, dự án và xu hướng thị trường hàng tuần."
        />
        <meta
          property="og:title"
          content="Thống kê thị trường giá bất động sản tại Việt Nam"
        />
        <meta
          property="og:description"
          content="Khám phá dữ liệu thị trường và biểu đồ giá bất động sản chi tiết tại Việt Nam."
        />
        <link rel="canonical" href="https://giabatdongsan.info.vn/" />
      </Helmet>
      <GoogleTag />
      <Header />
      <HeroSection />
      <BarChartsSection />
      <FeaturesSection />
      <TargetUsersSection />
      <AnalyticsSection />
      <UserTestimonials />

      <SEOTags />

      <Footer />
    </>
  );
}

export default TrangChu;
